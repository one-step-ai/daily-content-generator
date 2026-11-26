"""Idempotent cloud preflight; outputs only today's media availability, never credentials."""
import json
import os
from pathlib import Path
import urllib.request


def render_plan(ready, variant, cinematic):
    if variant == 0:
        return not ready['story'] or (not cinematic and not ready['business'])
    if variant == 1:
        return not ready['ugc']
    if variant == 2:
        return not cinematic and not ready['third']
    raise ValueError('Unknown video variant')

def main():
    key=os.environ.get('MARKETING_UPLOAD_KEY','');url=os.environ.get('MARKETING_UPLOAD_URL','')
    if not key or not url:raise RuntimeError('Scoped media configuration missing')
    req=urllib.request.Request(url.replace('mode=upload-video','mode=video-status'),data=b'{}',method='POST',headers={'Content-Type':'application/json','x-marketing-upload-key':key})
    with urllib.request.urlopen(req,timeout=30) as response:data=json.load(response)
    ready={name:data.get(name+'Ready') is True for name in ('business','ugc','story','podcast','third')}
    cinematic = data.get('robohubReelOrder') == 'cinematic'
    variant = os.environ.get('VIDEO_VARIANT')
    output=os.environ.get('GITHUB_OUTPUT')
    if output:
        with Path(output).open('a',encoding='utf-8') as f:
            for name,value in ready.items():f.write(name+'_ready='+str(value).lower()+'\n')
            f.write('cinematic_order='+str(cinematic).lower()+'\n')
            if variant is not None:
                f.write('render_needed='+str(render_plan(ready, int(variant), cinematic)).lower()+'\n')
    print(json.dumps(ready))

if __name__=='__main__':main()
