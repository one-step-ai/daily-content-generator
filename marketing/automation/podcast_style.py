"""Minimal podcast finish: full portrait, factual AI label, complete Arabic subtitles."""
import json
import math
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[2]


def render(source,metadata,target):
    import arabic_reshaper
    from bidi.algorithm import get_display
    from PIL import Image,ImageDraw,ImageFont
    from ugc_style import caption_chunks,active_cue
    data=json.loads(Path(metadata).read_text(encoding='utf-8'))
    duration=float(data['duration']);width,height,fps=720,1280,25
    ffmpeg=shutil.which('ffmpeg')
    if not ffmpeg:
        import imageio_ffmpeg
        ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    cache=ROOT/'state/marketing-cache'
    font=ImageFont.truetype(str(cache/'sora.ttf'),20)
    arabic=ImageFont.truetype(str(cache/'arabic.ttf'),46,layout_engine=ImageFont.Layout.BASIC)
    target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
    decoder=subprocess.Popen([ffmpeg,'-v','error','-i',str(source),'-vf','scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,fps=25','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],stdout=subprocess.PIPE)
    encoder=subprocess.Popen([ffmpeg,'-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','720x1280','-r','25','-i','pipe:0','-i',str(source),'-map','0:v:0','-map','1:a:0','-t',str(duration),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-movflags','+faststart',str(target)],stdin=subprocess.PIPE)
    count=0
    try:
        while count<round(duration*fps):
            raw=bytearray()
            while len(raw)<width*height*3:
                part=decoder.stdout.read(width*height*3-len(raw))
                if not part:break
                raw.extend(part)
            if not raw:break
            if len(raw)!=width*height*3:raise RuntimeError('Incomplete podcast frame')
            image=Image.frombytes('RGB',(width,height),bytes(raw)).convert('RGBA')
            overlay=Image.new('RGBA',(width,height));draw=ImageDraw.Draw(overlay)
            draw.rounded_rectangle((38,72,682,114),radius=12,fill=(8,8,8,190))
            draw.text((54,82),'ONE STEP',font=font,fill='#D4AF37')
            draw.text((247,82),'FICTIONAL AI PRESENTER',font=font,fill='#F6F2E9')
            t=count/fps;cue=data['cues'][active_cue(data['cues'],t)]
            chunks=caption_chunks(cue['ar'],max_words=7)
            progress=max(0,min(.99999,(t-cue['start'])/(cue['end']-cue['start'])))
            chunk=chunks[min(len(chunks)-1,int(progress*len(chunks)))]
            lines=[];line=''
            for word in chunk.split():
                trial=(line+' '+word).strip()
                if line and draw.textlength(get_display(arabic_reshaper.reshape(trial)),font=arabic)>600:
                    lines.append(line);line=word
                else:line=trial
            if line:lines.append(line)
            y=1010-(len(lines)-1)*26
            draw.rounded_rectangle((38,y-15,682,y+len(lines)*54+9),radius=14,fill=(5,5,5,218))
            draw.rectangle((59,y-15,661,y-12),fill='#D4AF37')
            for i,text in enumerate(lines):
                text=get_display(arabic_reshaper.reshape(text))
                draw.text(((width-draw.textlength(text,font=arabic))/2,y+i*54),text,font=arabic,fill='#F6F2E9')
            image=Image.alpha_composite(image,overlay).convert('RGB')
            encoder.stdin.write(image.tobytes());count+=1
    finally:
        decoder.stdout.close();encoder.stdin.close()
        ds,es=decoder.wait(),encoder.wait()
    if ds or es or count<round(duration*fps)-2:raise RuntimeError('Podcast export incomplete')
    return {'path':str(target),'seconds':count/fps,'frames':count,'bytes':target.stat().st_size}
