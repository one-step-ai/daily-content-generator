"""Approved fox motion bank, fresh bilingual narration and free CPU finishing.

Reuses approved animation, not newly generated or precisely re-lip-synced footage.
No inference service, credit purchase, or hidden still-image fallback.
"""
from datetime import date
from pathlib import Path
import hashlib
import json
import math
import subprocess

ROOT = Path(__file__).resolve().parents[2]
TOPICS = [
 ('customer enquiries','استفسارات العملاء'),
 ('website enquiries','استفسارات الموقع الإلكتروني'),
 ('sales follow-ups','متابعات المبيعات'),
 ('customer requests','طلبات العملاء'),
 ('team handoffs','تسليم المهام بين أعضاء الفريق'),
 ('daily follow-ups','المتابعات اليومية'),
 ('contact forms','نماذج التواصل'),
 ('incoming messages','الرسائل الواردة'),
 ('routine tasks','المهام المتكررة'),
 ('lead tracking','تتبّع العملاء المحتملين'),
 ('customer conversations','محادثات العملاء'),
 ('business workflows','إجراءات العمل'),
]
BENEFITS = [
 ('Keep the next action clear.','اجعل الخطوة التالية واضحة.'),
 ('Give every request a clear owner.','حدّد مسؤولًا واضحًا عن كل طلب.'),
 ('Help your team stay organised.','ساعد فريقك على تنظيم العمل.'),
 ('Keep customer context together.','احتفظ بتفاصيل طلبات العملاء في مكان واحد.'),
 ('Start with one useful workflow.','ابدأ بمسار عمل واحد مفيد.'),
 ('Make routine handoffs easier.','سهّل تسليم المهام المتكررة.'),
]
CTAS = [
 ('Message One Step today.','راسل ون ستيب اليوم.'),
 ('Talk to One Step about your workflow.','تواصل مع ون ستيب بشأن إجراءات عملك.'),
 ('Tell One Step what your team needs.','أخبر ون ستيب بما يحتاجه فريقك.'),
 ('Discuss your next step with One Step.','ناقش خطوتك التالية مع ون ستيب.'),
]

def script(day, variant):
    if variant not in (0,1,2):
        raise ValueError('Three daily cartoon variants only')
    n=(date.fromisoformat(day)-date(2026,11,16)).days*3+variant
    # Exhaustion is explicit; do not rotate an old script and call it fresh.
    if not 0<=n<len(TOPICS)*len(BENEFITS)*len(CTAS):
        raise ValueError('Reviewed unique script bank needs replenishment')
    topic=TOPICS[n%len(TOPICS)]
    benefit=BENEFITS[(n//len(TOPICS))%len(BENEFITS)]
    cta=CTAS[n//(len(TOPICS)*len(BENEFITS))]
    cues=[{'en':f'One Step connects {topic[0]} with websites, CRM systems, and business automation.',
           'ar':f'تربط ون ستيب {topic[1]} بالمواقع الإلكترونية وأنظمة إدارة العملاء وحلول أتمتة الأعمال.'},
          {'en':benefit[0],'ar':benefit[1]}, {'en':cta[0],'ar':cta[1]}]
    fingerprint=hashlib.sha256(json.dumps(cues,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return {'day':day,'variant':variant,'title':topic[0].capitalize(), 'cues':cues,
            'script_sha256':fingerprint,'fictional_ai_presenter':True,
            'format':'approved-cinematic-fox','reused_approved_motion':True,'lip_sync_verified':False}

def render(day, variant=0, target=None):
    import numpy as np
    import soundfile as sf
    import imageio_ffmpeg
    from kokoro_onnx import Kokoro
    from fox_caption_style import render as finish
    from daily_video import CACHE, OUT
    OUT.mkdir(parents=True,exist_ok=True)
    stem=day+(['','-second','-third'][variant])
    target=Path(target) if target else OUT/(stem+'.mp4')
    meta=OUT/(stem+'.json');data=script(day,variant)
    if target.exists():
        old=json.loads(meta.read_text(encoding='utf8'))
        if old.get('script_sha256')!=data['script_sha256']:
            raise ValueError('Existing media uses a different script; preserve and review')
        return target
    model=Kokoro(str(CACHE/'kokoro-v1.0.int8.onnx'),str(CACHE/'voices-v1.0.bin'))
    for speed in (1.0,1.08,1.16):
        parts=[];clock=0
        for cue in data['cues']:
            audio,rate=model.create(cue['en'],voice='am_michael',speed=speed,lang='en-us')
            audio=np.concatenate([audio,np.zeros(round(rate*.12),dtype=np.float32)])
            cue.update(start=clock,end=clock+len(audio)/rate);clock=cue['end'];parts.append(audio)
        if clock<=15:break
    if clock>15:raise ValueError('Narration exceeds 15 seconds; revise script')
    duration=max(10,math.ceil(clock*25)/25)
    samples=np.concatenate(parts);samples=np.pad(samples,(0,round(duration*rate)-len(samples)))
    wav=OUT/(stem+'.wav');sf.write(wav,samples,rate)
    data.update(duration=duration,voice='am_michael',voice_speed=speed)
    data['cues'][-1]['end']=duration
    meta.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
    f=imageio_ffmpeg.get_ffmpeg_exe();assets=ROOT/'marketing/automation/assets'
    raw=OUT/(stem+'-raw.mp4')
    subprocess.run([f,'-y','-v','error','-i',str(assets/'approved-fox-opening.mp4'),
        '-i',str(assets/'approved-fox-continuation.mp4'),'-i',str(wav),'-filter_complex',
        '[0:v]trim=duration=5,setpts=PTS-STARTPTS,scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1,fps=25[v0];'
        '[1:v]setpts=PTS-STARTPTS,scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1,fps=25[v1];'
        '[v0][v1]concat=n=2:v=1:a=0,eq=contrast=1.045:saturation=1.06:gamma=1.025[v]',
        '-map','[v]','-map','2:a:0','-t',str(duration),'-c:v','libx264','-pix_fmt','yuv420p',
        '-c:a','aac',str(raw)],check=True)
    finish(raw,meta,target)
    subprocess.run([f,'-v','error','-i',str(target),'-f','null','-'],check=True)
    return target
