"""Fetch pinned upstream source and hash-verified public CPU model files."""
import hashlib
import argparse
from pathlib import Path
import subprocess
import urllib.request

ROOT=Path(__file__).resolve().parents[2]
REVISION='cd4c0465ae0b54a6f85af57f5c65fec9fe23e7f8'
MODELS={
 'mapping_00109-model.pth.tar':'84a8642468a3fcfdd9ab6be955267043116c2bec2284686a5262f1eaf017f64c',
 'mapping_00229-model.pth.tar':'62a1e06006cc963220f6477438518ed86e9788226c62ae382ddc42fbcefb83f1',
 'SadTalker_V0.0.2_256.safetensors':'c211f5d6de003516bf1bbda9f47049a4c9c99133b1ab565c6961e5af16477bff',
 'SadTalker_V0.0.2_512.safetensors':'0e063f7ff5258240bdb0f7690783a7b1374e6a4a81ce8fa33456f4cd49694340'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--size',type=int,choices=(256,512),default=256);args=p.parse_args()
    target=ROOT/'state/SadTalker';target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():subprocess.run(['git','clone','https://github.com/OpenTalker/SadTalker.git',str(target)],check=True)
    subprocess.run(['git','checkout','--detach',REVISION],cwd=target,check=True)
    checkpoint=target/'checkpoints';checkpoint.mkdir(exist_ok=True)
    for name,digest in MODELS.items():
        if name.startswith('SadTalker_') and f'_{args.size}.' not in name:continue
        path=checkpoint/name
        if not path.exists():
            temporary=path.with_suffix(path.suffix+'.download')
            with urllib.request.urlopen('https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/'+name,timeout=90) as r,temporary.open('wb') as f:
                while chunk:=r.read(1024*1024):f.write(chunk)
            temporary.replace(path)
        h=hashlib.sha256()
        with path.open('rb') as f:
            while chunk:=f.read(1024*1024):h.update(chunk)
        if h.hexdigest()!=digest:raise RuntimeError('Model checksum mismatch: '+name)
        print('Verified',name)

if __name__=='__main__':main()
