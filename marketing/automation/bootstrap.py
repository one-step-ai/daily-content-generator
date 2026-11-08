"""Download the project's free, versioned rendering assets; never uses an API key."""
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / 'state' / 'marketing-cache'
RELEASE = 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/'
ASSETS = {
    'kokoro-v1.0.int8.onnx': RELEASE + 'kokoro-v1.0.int8.onnx',
    'voices-v1.0.bin': RELEASE + 'voices-v1.0.bin',
    'inter.ttf': 'https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz,wght%5D.ttf',
    'sora.ttf': 'https://raw.githubusercontent.com/google/fonts/main/ofl/sora/Sora%5Bwght%5D.ttf',
    'arabic.ttf': 'https://raw.githubusercontent.com/google/fonts/main/ofl/notonaskharabic/NotoNaskhArabic%5Bwght%5D.ttf',
    'inter-OFL.txt': 'https://raw.githubusercontent.com/google/fonts/main/ofl/inter/OFL.txt',
    'sora-OFL.txt': 'https://raw.githubusercontent.com/google/fonts/main/ofl/sora/OFL.txt',
    'arabic-OFL.txt': 'https://raw.githubusercontent.com/google/fonts/main/ofl/notonaskharabic/OFL.txt',
}

def ensure_assets():
    CACHE.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name, url in ASSETS.items():
        path = CACHE / name
        if not path.exists() or path.stat().st_size < 100:
            temporary = path.with_suffix(path.suffix + '.part')
            with urllib.request.urlopen(url, timeout=90) as response, temporary.open('wb') as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
            temporary.replace(path)
        manifest[name] = {'url': url, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size}
        print(name, manifest[name]['bytes'], flush=True)
    (CACHE / 'assets.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return CACHE

if __name__ == '__main__':
    ensure_assets()
