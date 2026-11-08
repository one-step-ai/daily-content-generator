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

def ass_time(seconds):
    centis=round(seconds*100)
    return f'{centis//360000}:{centis//6000%60:02}:{centis//100%60:02}.{centis%100:02}'

def main():
    p=argparse.ArgumentParser();p.add_argument('--sadtalker',required=True);p.add_argument('--finish-only',action='store_true');p.add_argument('--render-only',action='store_true');a=p.parse_args()
    day=datetime.now(timezone(timedelta(hours=4))).date().isoformat()
    out=ROOT/'state/daily-marketing';data=json.loads((out/(day+'-ugc.json')).read_text(encoding='utf-8'))
    target=out/(day+'-ugc.mp4');receipt=out/(day+'-ugc.uploaded.json')
    if receipt.exists():return
    if not target.exists():
        sadtalker=Path(a.sadtalker).resolve();results=out/(day+'-ugc-render');results.mkdir(exist_ok=True)
        if not a.finish_only:
            env=dict(os.environ,OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4')
            subprocess.run([sys.executable,'inference.py','--cpu','--size','256','--batch_size','1','--preprocess','full','--still',
              '--source_image',str(ROOT/'marketing/automation/assets/fictional-presenter.png'),
              '--driven_audio',str(out/(day+'-ugc.wav')),'--result_dir',str(results)],cwd=sadtalker,env=env,check=True)
        raw=max(results.glob('*.mp4'),key=lambda f:f.stat().st_mtime)
        subtitles=out/(day+'-ugc.ass')
        lines=['[Script Info]','ScriptType: v4.00+','PlayResX: 720','PlayResY: 1280','WrapStyle: 0','[V4+ Styles]',
          'Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding',
          'Style: Subtitle,Noto Naskh Arabic,35,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,3,1,0,2,50,50,220,1',
          'Style: Label,Sora,19,&H0037AFD4,&H0037AFD4,&H00000000,&H70000000,0,0,0,0,100,100,0,0,3,1,0,8,40,40,100,1',
          '[Events]','Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text',
          'Dialogue: 1,0:00:00.00,'+ass_time(data['duration'])+',Label,,0,0,0,,ONE STEP | FICTIONAL AI PRESENTER']
        for cue in data['cues']:
            text=cue['ar'].replace('{','').replace('}','').replace('\n',' ')
            lines.append(f"Dialogue: 0,{ass_time(cue['start'])},{ass_time(cue['end'])},Subtitle,,0,0,0,,{text}")
        subtitles.write_text('\n'.join(lines)+'\n',encoding='utf-8')
        # Relative filter paths avoid shell interpolation and Windows path escaping.
        relative_ass=subtitles.relative_to(ROOT).as_posix()
        filters='scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,ass='+relative_ass+':fontsdir=state/marketing-cache'
        temporary=out/(day+'-ugc.encoding.mp4')
        subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(raw),'-vf',filters,'-c:v','libx264','-preset','fast','-crf','23','-pix_fmt','yuv420p','-c:a','aac','-b:a','96k','-movflags','+faststart',str(temporary)],cwd=ROOT,check=True)
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
