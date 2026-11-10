"""A short story from the tutorial's complete opening and complete call to action."""
import json
from pathlib import Path
import subprocess


def create(source, metadata, target):
    import imageio_ffmpeg
    data = json.loads(Path(metadata).read_text(encoding='utf-8'))
    first = data['cues'][0]['end']
    closing = data['cues'][-1]['start']
    end = data['duration']
    if not 3 <= first+end-closing <= 60:
        raise ValueError('Story must fit the supported short-video bound')
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    graph = (f'[0:v]trim=start=0:end={first},setpts=PTS-STARTPTS[v0];'
             f'[0:a]atrim=start=0:end={first},asetpts=PTS-STARTPTS[a0];'
             f'[0:v]trim=start={closing}:end={end},setpts=PTS-STARTPTS[v1];'
             f'[0:a]atrim=start={closing}:end={end},asetpts=PTS-STARTPTS[a1];'
             '[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]')
    subprocess.run([ff, '-y', '-v', 'error', '-i', str(source), '-filter_complex', graph,
                    '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-preset', 'fast',
                    '-crf', '19', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k',
                    '-movflags', '+faststart', str(target)], check=True)
    subprocess.run([ff, '-v', 'error', '-i', str(target), '-f', 'null', '-'], check=True)
    return Path(target)
