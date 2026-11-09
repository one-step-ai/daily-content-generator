"""Free editorial finish for the fictional presenter; preserves source speech."""
import argparse
import json
import math
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / 'state/marketing-cache'
W, H, FPS = 720, 1280, 25


def caption_chunks(text, max_words=6):
    words = text.split()
    return [' '.join(words[i:i+max_words]) for i in range(0, len(words), max_words)] or ['']


def active_cue(cues, seconds):
    return next((i for i, c in enumerate(cues) if c['start'] <= seconds < c['end']), len(cues)-1)


def render(source, metadata, target, seconds=None, offset=0):
    import arabic_reshaper
    from bidi.algorithm import get_display
    from PIL import Image, ImageDraw, ImageFont

    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    data = json.loads(Path(metadata).read_text(encoding='utf-8'))
    duration = min(float(data['duration'])-offset, seconds or float(data['duration']))
    if duration <= 0:
        raise ValueError('No source duration remains')
    cues = data['cues']
    fonts = {s: ImageFont.truetype(str(CACHE/'sora.ttf'), s) for s in (20, 22, 25, 28, 32, 40)}
    arfont = ImageFont.truetype(str(CACHE/'arabic.ttf'), 53)
    gold, ivory = (226, 188, 87, 255), (250, 249, 246, 255)
    target = Path(target); target.parent.mkdir(parents=True, exist_ok=True)
    decoder = subprocess.Popen([ffmpeg, '-v', 'error', '-ss', str(offset), '-i', str(source),
        '-t', str(duration), '-vf', 'scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,fps=25',
        '-f', 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:1'], stdout=subprocess.PIPE)
    encoder = subprocess.Popen([ffmpeg, '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
        '-s', '720x1280', '-r', str(FPS), '-i', 'pipe:0', '-ss', str(offset), '-i', str(source),
        '-map', '0:v:0', '-map', '1:a:0', '-t', str(duration), '-c:v', 'libx264', '-preset', 'fast',
        '-crf', '18', '-maxrate', '1500k', '-bufsize', '3000k', '-pix_fmt', 'yuv420p',
        '-c:a', 'copy', '-movflags', '+faststart', str(target)], stdin=subprocess.PIPE)

    def centered(draw, text, y, font, fill=ivory):
        draw.text(((W-draw.textlength(text,font=font))/2,y),text,font=font,fill=fill)

    def fit(draw, text, max_width=572, start=32):
        for size in range(start,19,-1):
            font=ImageFont.truetype(str(CACHE/'sora.ttf'),size)
            if draw.textlength(text,font=font)<=max_width:return font
        return fonts[20]

    frame_count=0
    try:
        while True:
            raw=bytearray()
            while len(raw)<W*H*3:
                chunk=decoder.stdout.read(W*H*3-len(raw))
                if not chunk:break
                raw.extend(chunk)
            if not raw:break
            if len(raw)!=W*H*3:raise RuntimeError('Incomplete video frame')
            t=offset+frame_count/FPS;ci=active_cue(cues,t);cue=cues[ci]
            progress=max(0,min(1,(t-cue['start'])/max(.01,cue['end']-cue['start'])))
            im=Image.frombytes('RGB',(W,H),bytes(raw)).convert('RGBA')
            # A restrained push-in changes at each thought; facial motion remains audio-driven.
            zoom=1+.025*progress
            enlarged=im.resize((round(W*zoom),round(H*zoom)),Image.Resampling.LANCZOS)
            left=(enlarged.width-W)//2;top=round((enlarged.height-H)*.28)
            im=enlarged.crop((left,top,left+W,top+H))
            overlay=Image.new('RGBA',(W,H));d=ImageDraw.Draw(overlay)
            # Covers the legacy tiny label in sample input; native new renders have no baked labels.
            d.rounded_rectangle((64,67,656,153),radius=22,fill=(13,17,21,247))
            d.text((88,89),'ONE STEP',font=fonts[28],fill=gold)
            d.text((328,94),'FICTIONAL AI PRESENTER',font=fonts[20],fill=ivory)
            d.rectangle((89,136,631,139),fill=(226,188,87,90))
            # Lower-third information replaces the old tiny subtitles, inside Reels safe areas.
            for y in range(740,950):
                a=round(240*(y-740)/210)
                d.line((0,y,W,y),fill=(10,15,20,a),width=1)
            d.rectangle((0,950,W,H),fill=(10,15,20,250))
            intro=ci==0;closing=len(cues)>1 and ci==len(cues)-1
            label='BUSINESS, ORGANISED' if intro else 'LET’S BUILD YOUR NEXT STEP' if closing else f'PRACTICAL STEP {min(ci,3):02}'
            d.text((64,815),label,font=fonts[20],fill=gold)
            title='Turn enquiries into next steps' if intro else 'Websites. CRM. Automation.' if closing else cue['en'].split('.')[0]+'.'
            d.text((64,850),title,font=fit(d,title),fill=ivory)
            # A small animated process diagram illustrates the idea without fictional client data.
            if not closing:
                names=['ENQUIRY','OWNER','NEXT ACTION']
                for j,name in enumerate(names):
                    x=64+j*200;selected=j==min(2,int(progress*3))
                    d.rounded_rectangle((x,912,x+176,961),radius=11,fill=gold if selected else (31,40,48,255))
                    font=fonts[20];tw=d.textlength(name,font=font)
                    d.text((x+(176-tw)/2,924),name,font=font,fill=(12,18,22,255) if selected else ivory)
                    if j<2:d.line((x+181,936,x+194,936),fill=gold,width=2)
            else:
                d.rounded_rectangle((64,908,656,968),radius=13,fill=gold)
                centered(d,'MESSAGE ONE STEP',924,fonts[25],(12,18,22,255))
            chunks=caption_chunks(cue['ar']);chunk=chunks[min(len(chunks)-1,int(progress*len(chunks)))]
            lines=[];line=''
            for word in chunk.split():
                trial=(line+' '+word).strip()
                if line and d.textlength(get_display(arabic_reshaper.reshape(trial)),font=arfont)>592:
                    lines.append(line);line=word
                else:line=trial
            if line:lines.append(line)
            for row,line in enumerate(lines):
                centered(d,get_display(arabic_reshaper.reshape(line)),990+row*59,arfont)
            d.rounded_rectangle((64,1120,656,1124),radius=2,fill=(65,73,78,255))
            d.rounded_rectangle((64,1120,65+int(591*min(1,t/data['duration'])),1124),radius=2,fill=gold)
            im=Image.alpha_composite(im,overlay).convert('RGB')
            encoder.stdin.write(im.tobytes());frame_count+=1
    finally:
        decoder.stdout.close();encoder.stdin.close()
        decoder_status=decoder.wait();encoder_status=encoder.wait()
    if decoder_status or encoder_status or frame_count<round(duration*FPS)-2:
        raise RuntimeError('Editorial export failed')
    if target.stat().st_size>12000000:raise RuntimeError('Export exceeds free media bound')
    return {'frames':frame_count,'seconds':frame_count/FPS,'bytes':target.stat().st_size,'path':str(target)}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--metadata',required=True)
    p.add_argument('--output',required=True);p.add_argument('--seconds',type=float);p.add_argument('--offset',type=float,default=0)
    a=p.parse_args();print(json.dumps(render(a.source,a.metadata,a.output,a.seconds,a.offset)))
