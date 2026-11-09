"""Pinned, commercially usable MuseTalk components; no service or GPU purchase."""
import hashlib
from pathlib import Path
import subprocess
import urllib.request

ROOT=Path(__file__).resolve().parents[2]
REVISION='0a89dec45a0192b824e3cf4daf96c239440c5ed8'
FILES=[
 ('TMElyralab/MuseTalk','2bcb936e2fddb4d86db4c62fd45b387d0c061571','musetalkV15/unet.pth','musetalkV15/unet.pth','7ebf6c98c181e20838e4c0054e96e944ac60d5d692cc01db42839fe11b787007'),
 ('TMElyralab/MuseTalk','2bcb936e2fddb4d86db4c62fd45b387d0c061571','musetalkV15/musetalk.json','musetalkV15/musetalk.json',None),
 ('stabilityai/sd-vae-ft-mse','31f26fdeee1355a5c34592e401dd41e45d25a493','diffusion_pytorch_model.bin','sd-vae/diffusion_pytorch_model.bin','1b4889b6b1d4ce7ae320a02dedaeff1780ad77d415ea0d744b476155c6377ddc'),
 ('stabilityai/sd-vae-ft-mse','31f26fdeee1355a5c34592e401dd41e45d25a493','config.json','sd-vae/config.json',None),
 ('openai/whisper-tiny','169d4a4341b33bc18d8881c4b69c2e104e1cc0af','pytorch_model.bin','whisper/pytorch_model.bin','9607f98a2b22d9e229ae43c52ecea79dcede9e0c5cfae67e8da6eda86d8aac1d'),
 ('openai/whisper-tiny','169d4a4341b33bc18d8881c4b69c2e104e1cc0af','config.json','whisper/config.json',None),
 ('openai/whisper-tiny','169d4a4341b33bc18d8881c4b69c2e104e1cc0af','preprocessor_config.json','whisper/preprocessor_config.json',None),
]


def main():
    source=ROOT/'state/MuseTalk'
    if not source.exists():subprocess.run(['git','clone','https://github.com/TMElyralab/MuseTalk.git',str(source)],check=True)
    subprocess.run(['git','checkout','--detach',REVISION],cwd=source,check=True)
    for repo,revision,name,destination,digest in FILES:
        path=source/'models'/destination;path.parent.mkdir(parents=True,exist_ok=True)
        if not path.exists():
            temporary=path.with_suffix(path.suffix+'.download')
            request=urllib.request.Request(f'https://huggingface.co/{repo}/resolve/{revision}/{name}?download=true',headers={'User-Agent':'OneStep-OpenSourceRenderer/1.0'})
            with urllib.request.urlopen(request,timeout=120) as r,temporary.open('wb') as output:
                while chunk:=r.read(1024*1024):output.write(chunk)
            temporary.replace(path)
        if digest:
            h=hashlib.sha256()
            with path.open('rb') as f:
                while chunk:=f.read(1024*1024):h.update(chunk)
            actual=h.hexdigest()
            if actual!=digest:raise RuntimeError('Model checksum mismatch: '+destination)
        print('Verified pinned model component',destination,flush=True)


if __name__=='__main__':main()
