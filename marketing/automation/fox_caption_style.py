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
    font=ImageFont.truetype(str(cache/'sora.ttf'),17)
    arabic=ImageFont.truetype(str(Path('C:/Windows/Fonts/arialbd.ttf') if Path('C:/Windows/Fonts/arialbd.ttf').exists() else cache/'arabic.ttf'),48,layout_engine=ImageFont.Layout.BASIC)
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
            # Compact brand signature with a separate, visible AI disclosure.
            gold='#D4AF37'
            draw.rounded_rectangle((38,58,682,146),radius=22,fill=(10,12,15,225),outline=(212,175,55,95),width=1)
            draw.rounded_rectangle((54,74,110,130),radius=14,fill=(27,25,18,255))
            for x,y,h in [(66,107,11),(77,96,22),(88,85,33)]:
                draw.rounded_rectangle((x,y,x+8,y+h),radius=2,fill=gold)
            brand=ImageFont.truetype(str(cache/'sora.ttf'),25)
            small=ImageFont.truetype(str(cache/'sora.ttf'),11)
            badge=ImageFont.truetype(str(cache/'sora.ttf'),13)
            draw.text((126,77),'ONE STEP',font=brand,fill='#F9F4E8')
            draw.text((127,112),'BUSINESS SOLUTIONS',font=small,fill=gold)
            draw.rounded_rectangle((486,84,661,121),radius=18,fill=(27,25,18,255),outline=(212,175,55,85))
            draw.ellipse((499,99,505,105),fill=gold)
            draw.text((516,94),'FICTIONAL AI',font=badge,fill='#EAE1CA')
            t=count/fps;cue=data['cues'][active_cue(data['cues'],t)]
            chunks=caption_chunks(cue['ar'],max_words=4)
            progress=max(0,min(.99999,(t-cue['start'])/(cue['end']-cue['start'])))
            chunk=chunks[min(len(chunks)-1,int(progress*len(chunks)))]
            lines=[];line=''
            for word in chunk.split():
                trial=(line+' '+word).strip()
                if line and draw.textlength(get_display(arabic_reshaper.reshape(trial)),font=arabic)>570:
                    lines.append(line);line=word
                else:line=trial
            if line:lines.append(line)
            display=[get_display(arabic_reshaper.reshape(line)) for line in lines]
            maxw=max(draw.textlength(line,font=arabic) for line in display)
            boxw=min(644,max(280,maxw+66));left=(720-boxw)/2
            top=1000-(len(lines)-1)*29;bottom=top+len(lines)*62+34
            draw.rounded_rectangle((left,top,left+boxw,bottom),radius=22,fill=(8,10,13,235),outline=(212,175,55,90),width=1)
            draw.rounded_rectangle((320,top-2,400,top+2),radius=2,fill=gold)
            for i,text in enumerate(display):
                color=gold if i==len(display)-1 else '#FFF8E9'
                draw.text(((width-draw.textlength(text,font=arabic))/2,top+19+i*62),text,font=arabic,fill=color,stroke_width=1,stroke_fill=color)
            image=Image.alpha_composite(image,overlay).convert('RGB')
            encoder.stdin.write(image.tobytes());count+=1
    finally:
        decoder.stdout.close();encoder.stdin.close()
        ds,es=decoder.wait(),encoder.wait()
    if ds or es or count<round(duration*fps)-2:raise RuntimeError('Podcast export incomplete')
    return {'path':str(target),'seconds':count/fps,'frames':count,'bytes':target.stat().st_size}

