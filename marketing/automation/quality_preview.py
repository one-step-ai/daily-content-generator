"""Prepare a six-second visual test from existing audio; never posts or changes speech."""
import argparse
import json
from pathlib import Path
import subprocess
import urllib.request
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[2]


def main():
    p=argparse.ArgumentParser();p.add_argument('source_url');p.add_argument('--full-metadata');args=p.parse_args()
    url=urlparse(args.source_url)
    if url.scheme!='https' or not url.hostname or not url.hostname.endswith('.supabase.co') or not url.path.startswith('/storage/v1/object/public/marketing-ugc/'):
        raise ValueError('An existing public marketing UGC asset is required')
    out=ROOT/'state/quality-preview';out.mkdir(parents=True,exist_ok=True)
    with urllib.request.urlopen(args.source_url,timeout=60) as r,(out/'source.mp4').open('wb') as f:
        n=0
        while chunk:=r.read(1024*1024):
            n+=len(chunk)
            if n>12000000:raise ValueError('Unexpected source size')
            f.write(chunk)
    if args.full_metadata:
        path=Path(args.full_metadata);data=json.loads(path.read_text(encoding='utf-8'))
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(out/'source.mp4')],text=True))
        duration=float(probe['format']['duration'])
        if not 30<=duration<=90 or abs(duration-data['duration'])>1:raise ValueError('Original speech does not match the reviewed script timeline')
        data['duration']=duration;data['cues'][-1]['end']=duration
        path.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
        subprocess.run(['ffmpeg','-y','-v','error','-i',str(out/'source.mp4'),'-vn','-ar','16000',str(path.with_suffix('.wav'))],check=True)
        return
    subprocess.run(['ffmpeg','-y','-v','error','-i',str(out/'source.mp4'),'-t','6','-vn','-ar','16000',str(out/'speech.wav')],check=True)
    (out/'metadata.json').write_text(json.dumps({'duration':6,'cues':[{'start':0,'end':6,'en':'Turn enquiries into useful next steps.','ar':'فكرة عملية لتنظيم استفسارات العملاء في شركتك.'}], 'fictional_ai_presenter':True},ensure_ascii=False),encoding='utf-8')


if __name__=='__main__':main()
