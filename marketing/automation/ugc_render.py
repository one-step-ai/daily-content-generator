"""Render the fictional AI presenter with pinned open-source SadTalker on CPU."""
import argparse
from datetime import datetime,timezone,timedelta
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

ROOT=Path(__file__).resolve().parents[2]

def main():
    p=argparse.ArgumentParser();p.add_argument('--sadtalker',required=True);p.add_argument('--finish-only',action='store_true');p.add_argument('--render-only',action='store_true');p.add_argument('--size',type=int,choices=(256,512),default=512);a=p.parse_args()
    day=datetime.now(timezone(timedelta(hours=4))).date().isoformat()
    out=ROOT/'state/daily-marketing';data=json.loads((out/(day+'-ugc.json')).read_text(encoding='utf-8'))
    target=out/(day+'-ugc.mp4');receipt=out/(day+'-ugc.uploaded.json')
    if receipt.exists():return
    if not target.exists():
        sadtalker=Path(a.sadtalker).resolve();results=out/(day+'-ugc-render');results.mkdir(exist_ok=True)
        if not a.finish_only:
            env=dict(os.environ,OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4')
            subprocess.run([sys.executable,'inference.py','--cpu','--size',str(a.size),'--batch_size','1','--preprocess','full',
              '--source_image',str(ROOT/'marketing/automation/assets/fictional-presenter.png'),
              '--driven_audio',str(out/(day+'-ugc.wav')),'--result_dir',str(results)],cwd=sadtalker,env=env,check=True)
        raw=max(results.glob('*.mp4'),key=lambda f:f.stat().st_mtime)
        from ugc_style import render
        temporary=out/(day+'-ugc.encoding.mp4')
        render(raw,out/(day+'-ugc.json'),temporary)
        temporary.replace(target)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_type,codec_name,width,height','-of','json',str(target)],text=True))
    duration=float(probe['format']['duration'])
    if duration<30 or abs(duration-data['duration'])>1 or not any(s['codec_type']=='video' and s['codec_name']=='h264' and s.get('height')==1280 for s in probe['streams']) or not any(s['codec_type']=='audio' for s in probe['streams']):raise RuntimeError('UGC export validation failed')
    if target.stat().st_size>12000000:raise RuntimeError('UGC file exceeds upload bound')
    if a.render_only:
        print(json.dumps({'day':day,'ugc_rendered':True,'duration':duration}));return
    key=os.environ.get('MARKETING_UPLOAD_KEY','');url=os.environ.get('MARKETING_UPLOAD_URL','')
    if not key or not url:raise RuntimeError('Scoped upload configuration missing')
    url+='&kind=ugc' if '?' in url else '?kind=ugc'
    req=urllib.request.Request(url,data=target.read_bytes(),method='POST',headers={'Content-Type':'video/mp4','x-marketing-upload-key':key})
    with urllib.request.urlopen(req,timeout=90) as r:result=json.load(r)
    receipt.write_text(json.dumps(result),encoding='utf-8')
    print(json.dumps({'day':day,'ugc_uploaded':True,'duration':duration}))

if __name__=='__main__':main()
