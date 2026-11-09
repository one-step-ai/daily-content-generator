"""Prepare a six-second visual test from existing audio; never posts or changes speech."""
import argparse
import json
from pathlib import Path
import subprocess
import urllib.request
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[2]


def main():
    p=argparse.ArgumentParser();p.add_argument('source_url');args=p.parse_args()
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
    subprocess.run(['ffmpeg','-y','-v','error','-i',str(out/'source.mp4'),'-t','6','-vn','-ar','16000',str(out/'speech.wav')],check=True)
    (out/'metadata.json').write_text(json.dumps({'duration':6,'cues':[{'start':0,'end':6,'en':'Turn enquiries into useful next steps.','ar':'فكرة عملية لتنظيم استفسارات العملاء في شركتك.'}], 'fictional_ai_presenter':True},ensure_ascii=False),encoding='utf-8')


if __name__=='__main__':main()
