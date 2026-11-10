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


def normalize(source,target,cue,trim_start=0):
    # Global frame boundaries avoid accumulating a rounding error across the six shots.
    frames=round(cue['end']*25)-round(cue['start']*25)
    subprocess.run([ffmpeg(),'-y','-v','error','-ss',str(trim_start),'-i',str(source),'-an','-vf','fps=25,tpad=stop_mode=clone:stop_duration=1',
        '-frames:v',str(frames),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',str(target)],check=True)


def render_chunk(day,index,enhanced_motion=False,lip_python=None):
    _,data=metadata(day);cue=data['cues'][index]
    work=ROOT/'state/ugc-clips';work.mkdir(parents=True,exist_ok=True)
    wav=work/f'clip-{index}.wav'
    first=round(cue['start']*25);last=round(cue['end']*25)
    context=12 if enhanced_motion or lip_python else 0
    low=max(0,first-context);high=min(round(data['duration']*25),last+context)
    full_audio=ROOT/'state/daily-marketing'/(day+'-ugc.wav')
    subprocess.run([ffmpeg(),'-y','-v','error','-ss',str(low/25),'-i',str(full_audio),
        '-t',str((high-low)/25),'-ar','16000',str(wav)],check=True)
    results=work/f'render-{index}';sadtalker=ROOT/'state/SadTalker'
    command=[sys.executable,'inference.py']
    if enhanced_motion:
        command=[sys.executable,str(ROOT/'marketing/automation/head_motion.py'),'--motion-audio',str(full_audio),'--motion-offset',str(low/25)]
    subprocess.run(command+['--cpu','--size','512','--batch_size','1','--preprocess','full','--expression_scale','1.08' if enhanced_motion else '1.0',
        '--source_image',str(ROOT/'marketing/automation/assets/fictional-presenter.png'),
        '--driven_audio',str(wav),'--result_dir',str(results)],cwd=sadtalker,check=True)
    raw=max(results.glob('*.mp4'),key=lambda f:f.stat().st_mtime)
    refined=False
    if lip_python:
        standardized=work/f'context-{index}.mp4'
        subprocess.run([ffmpeg(),'-y','-v','error','-i',str(raw),'-an','-vf','scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,fps=25',
            '-c:v','libx264','-preset','fast','-crf','18',str(standardized)],check=True)
        candidate=work/f'lip-{index}.mp4'
        try:
            subprocess.run([lip_python,str(ROOT/'marketing/automation/lip_refine.py'),'--source',str(standardized),'--audio',str(wav),'--output',str(candidate)],check=True,timeout=3600)
            raw=candidate;refined=True
        except (subprocess.CalledProcessError,subprocess.TimeoutExpired):
            print('Dedicated lip stage unavailable; retaining the free audio-driven face render.',flush=True)
    normalize(raw,work/f'clip-{index}.mp4',cue,trim_start=(first-low)/25)
    (work/f'clip-{index}-quality.json').write_text(json.dumps({'enhanced_motion':enhanced_motion,'dedicated_lip_sync':refined,'context_frames':context}),encoding='utf-8')


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
    p.add_argument('--enhanced-motion',action='store_true');p.add_argument('--lip-python')
    a=p.parse_args()
    if a.mode=='render':
        if a.index is None:p.error('--index is required for a render')
        render_chunk(a.day,a.index,a.enhanced_motion,a.lip_python)
    else:assemble(a.day)
