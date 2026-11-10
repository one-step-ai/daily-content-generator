"""Idempotent cloud preflight; outputs only today's media availability, never credentials."""
import json
import os
from pathlib import Path
import urllib.request

def main():
    key=os.environ.get('MARKETING_UPLOAD_KEY','');url=os.environ.get('MARKETING_UPLOAD_URL','')
    if not key or not url:raise RuntimeError('Scoped media configuration missing')
    req=urllib.request.Request(url.replace('mode=upload-video','mode=video-status'),data=b'{}',method='POST',headers={'Content-Type':'application/json','x-marketing-upload-key':key})
    with urllib.request.urlopen(req,timeout=30) as response:data=json.load(response)
    ready={name:data.get(name+'Ready') is True for name in ('business','ugc','story','podcast')}
    output=os.environ.get('GITHUB_OUTPUT')
    if output:
        with Path(output).open('a',encoding='utf-8') as f:
            for name,value in ready.items():f.write(name+'_ready='+str(value).lower()+'\n')
    print(json.dumps(ready))

if __name__=='__main__':main()
