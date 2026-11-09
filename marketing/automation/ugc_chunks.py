"""Render six speech-aligned shots in parallel, then restore the uncut original audio."""
import argparse
from datetime import datetime,timezone,timedelta
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]


def ffmpeg():
    binary=shutil.which('ffmpeg')
    if binary:return binary
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def metadata(day):
    path=ROOT/'state/daily-marketing'/(day+'-ugc.json')
    data=json.loads(path.read_text(encoding='utf-8'))
    if len(data['cues'])!=6:raise ValueError('Six reviewed speech sections are required')
    return path,data


def normalize(source,target,cue):
    # Global frame boundaries avoid accumulating a rounding error across the six shots.
    frames=round(cue['end']*25)-round(cue['start']*25)
    subprocess.run([ffmpeg(),'-y','-v','error','-i',str(source),'-an','-vf','fps=25,tpad=stop_mode=clone:stop_duration=1',
        '-frames:v',str(frames),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',str(target)],check=True)


def render_chunk(day,index):
    _,data=metadata(day);cue=data['cues'][index]
    work=ROOT/'state/ugc-clips';work.mkdir(parents=True,exist_ok=True)
    wav=work/f'clip-{index}.wav'
    subprocess.run([ffmpeg(),'-y','-v','error','-ss',str(cue['start']),'-i',str(ROOT/'state/daily-marketing'/(day+'-ugc.wav')),
        '-t',str(cue['end']-cue['start']),'-ar','16000',str(wav)],check=True)
    results=work/f'render-{index}';sadtalker=ROOT/'state/SadTalker'
    subprocess.run([sys.executable,'inference.py','--cpu','--size','512','--batch_size','1','--preprocess','full',
        '--source_image',str(ROOT/'marketing/automation/assets/fictional-presenter.png'),
        '--driven_audio',str(wav),'--result_dir',str(results)],cwd=sadtalker,check=True)
    raw=max(results.glob('*.mp4'),key=lambda f:f.stat().st_mtime)
    normalize(raw,work/f'clip-{index}.mp4',cue)


def assemble(day):
    meta,data=metadata(day);work=ROOT/'state/ugc-clips';clips=[work/f'clip-{i}.mp4' for i in range(6)]
    if not all(p.is_file() and p.stat().st_size>1000 for p in clips):raise ValueError('All six rendered shots are required')
    concat=work/'shots.txt'
    concat.write_text(''.join("file '"+p.name+"'\n" for p in clips),encoding='utf-8')
    joined=work/'presenter-with-original-audio.mp4'
    subprocess.run([ffmpeg(),'-y','-v','error','-f','concat','-safe','0','-i',str(concat),
        '-i',str(ROOT/'state/daily-marketing'/(day+'-ugc.wav')),'-map','0:v:0','-map','1:a:0',
        '-c:v','copy','-c:a','aac','-b:a','128k','-movflags','+faststart',str(joined)],check=True)
    from ugc_style import render
    target=ROOT/'state/daily-marketing'/(day+'-ugc.mp4')
    print(json.dumps(render(joined,meta,target)))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=('render','assemble'));p.add_argument('--day',default=datetime.now(timezone(timedelta(hours=4))).date().isoformat());p.add_argument('--index',type=int,choices=range(6))
    a=p.parse_args()
    if a.mode=='render':
        if a.index is None:p.error('--index is required for a render')
        render_chunk(a.day,a.index)
    else:assemble(a.day)
