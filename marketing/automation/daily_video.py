"""Free daily business-tip reel: local Kokoro voice + Pillow graphics + bundled FFmpeg.

The upload credential is scoped to today's video and protected with Windows DPAPI.
No inference API, subscription, stock footage or paid generation is used.
"""
import argparse
import base64
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone, timedelta
import hashlib
import json
import math
import os
from pathlib import Path
import secrets
import subprocess
import textwrap
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / 'state' / 'marketing-cache'
OUT = ROOT / 'state' / 'daily-marketing'
CONFIG = ROOT / 'state' / 'marketing-upload.dpapi'
API = os.environ.get('MARKETING_UPLOAD_URL','https://dvqssvbkpnklnzzsdcjj.supabase.co/functions/v1/marketing-auto?mode=upload-video')

# Each item is reviewed instructional content, not a claim about a prospect or client result.
TIPS = [
 ('Give every lead a next action', ['Capture the enquiry in one place.', 'Assign one person to own the next step.', 'Write the follow-up task and its due date.'], ['اجمع استفسارات العملاء في مكان واحد.', 'حدد المسؤول عن الخطوة التالية.', 'سجل مهمة المتابعة وموعدها.']),
 ('Make your contact page work harder', ['State the services your business offers.', 'Give visitors one clear way to contact you.', 'Send each enquiry into a trackable workflow.'], ['وضح الخدمات التي تقدمها شركتك.', 'اجعل التواصل معك سهلاً وواضحاً.', 'اربط كل استفسار بعملية متابعة منظمة.']),
 ('Stop relying on memory for follow-ups', ['Record what the customer asked for.', 'Choose the next useful action.', 'Set a reminder with a named owner.'], ['سجل ما يطلبه العميل.', 'حدد الخطوة التالية المناسبة.', 'أضف تذكيراً وحدد المسؤول.']),
 ('Clean your pipeline before automating', ['Define what each sales stage means.', 'Keep the latest conversation with the lead.', 'Move the record when a real event happens.'], ['حدد معنى كل مرحلة في المبيعات.', 'احتفظ بآخر محادثة مع العميل.', 'حدث المرحلة بناءً على تقدم حقيقي.']),
 ('Build a clearer team handoff', ['Pass the customer context with the task.', 'Name the receiving owner.', 'Confirm that the next step was accepted.'], ['انقل تفاصيل العميل مع المهمة.', 'حدد الشخص الذي يستلم المتابعة.', 'تأكد من استلام الخطوة التالية.']),
 ('Automate one repeated task first', ['Choose a task your team repeats often.', 'Write its trigger and decision rules.', 'Test the result before expanding the workflow.'], ['اختر مهمة متكررة في عملك.', 'حدد متى تبدأ وقواعد تنفيذها.', 'اختبر النتيجة قبل توسيع الأتمتة.']),
 ('Turn a reply into a useful next step', ['Save the conversation to the lead record.', 'Identify what the person actually needs.', 'Assign the next action to the right person.'], ['احفظ المحادثة في سجل العميل.', 'حدد ما يحتاجه العميل فعلاً.', 'وجه الخطوة التالية للشخص المناسب.']),
 ('Connect your form to follow-up', ['Ask only for the details you need.', 'Save the enquiry with its source.', 'Notify the person responsible for follow-up.'], ['اطلب المعلومات الضرورية فقط.', 'احفظ الاستفسار مع مصدره.', 'أبلغ المسؤول عن المتابعة.']),
 ('Make your sales stages useful', ['Use stage names your team understands.', 'Define the evidence needed to move forward.', 'Keep the next action visible at every stage.'], ['استخدم أسماء مراحل واضحة لفريقك.', 'حدد متى ينتقل العميل للمرحلة التالية.', 'اجعل الخطوة التالية واضحة دائماً.']),
 ('Map the process before choosing tools', ['Write the starting event.', 'List the handoffs and decisions.', 'Define what a completed result looks like.'], ['حدد نقطة بداية العملية.', 'سجل خطوات التسليم والقرارات.', 'حدد النتيجة المطلوبة بوضوح.']),
 ('Give your website one clear next step', ['Explain the service in plain language.', 'Put contact details where people can find them.', 'Connect incoming requests to your team.'], ['اشرح الخدمة بلغة واضحة.', 'اجعل بيانات التواصل سهلة الوصول.', 'اربط طلبات العملاء بفريقك.']),
 ('Keep customer context together', ['Store the correct contact details.', 'Attach the latest conversation.', 'Record the next task with an owner.'], ['احفظ بيانات التواصل الصحيحة.', 'أرفق آخر محادثة مع العميل.', 'حدد المهمة التالية والمسؤول عنها.']),
 ('Build useful reminders', ['Tie the reminder to a real task.', 'Give it a clear due date.', 'Make the reminder reach the responsible person.'], ['اربط التذكير بمهمة حقيقية.', 'حدد موعداً واضحاً للتنفيذ.', 'أرسل التذكير للشخص المسؤول.']),
 ('Create a handoff checklist', ['Include the customer request.', 'Include what has already been done.', 'Include the next decision and its owner.'], ['أضف طلب العميل إلى قائمة التسليم.', 'وضح ما تم تنفيذه بالفعل.', 'حدد القرار التالي والمسؤول عنه.']),
 ('Make enquiry tracking a daily habit', ['Review new enquiries in one place.', 'Check that every active lead has a next step.', 'Close outdated tasks and update the record.'], ['راجع الاستفسارات الجديدة في مكان واحد.', 'تأكد من وجود خطوة تالية لكل عميل.', 'حدث المهام والسجلات باستمرار.']),
]


class Blob(ctypes.Structure):
    _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]


def protect(data, decrypt=False):
    buf = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_ubyte)))
    target = Blob()
    fn = ctypes.windll.crypt32.CryptUnprotectData if decrypt else ctypes.windll.crypt32.CryptProtectData
    if not fn(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target)):
        raise RuntimeError('Windows credential protection failed')
    try:
        return ctypes.string_at(target.data, target.size)
    finally:
        ctypes.windll.kernel32.LocalFree(target.data)


def setup():
    OUT.mkdir(parents=True, exist_ok=True)
    if CONFIG.exists():
        key = protect(CONFIG.read_bytes(), True)
    else:
        key = secrets.token_urlsafe(40).encode()
        CONFIG.write_bytes(protect(key))
    print(json.dumps({'sha256': hashlib.sha256(key).hexdigest()}))


def render(day):
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    import soundfile as sf
    import imageio_ffmpeg
    from kokoro_onnx import Kokoro
    import arabic_reshaper
    from bidi.algorithm import get_display

    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / (day + '.mp4')
    if target.exists() and target.stat().st_size > 10000:
        return target
    n = (datetime.fromisoformat(day) - datetime(1970, 1, 1)).days
    title, steps, arabic = TIPS[n % len(TIPS)]
    segments = [
        ('BUSINESS HACK', title, 'نصيحة عملية لتنظيم أعمالك', 'Here is a practical business tip from One Step. ' + title + '.'),
        *[(f'STEP {i+1}', step, ar, step + ' Keep it simple enough that your team can use it consistently.') for i, (step, ar) in enumerate(zip(steps, arabic))],
        ('PUT IT INTO PRACTICE', 'Start small. Test it. Improve it.', 'ابدأ بخطوة بسيطة واختبر النتيجة.', 'Start with one workflow, test it with a real enquiry, and check the result before you expand it.'),
        ('ONE STEP', 'Websites. CRM. Business automation.', 'راسل ون ستيب لمناقشة احتياجات شركتك.', 'One Step builds websites, CRM systems and enquiry automations. Message us to discuss how your business process could be organised.')
    ]
    kokoro = Kokoro(str(CACHE/'kokoro-v1.0.int8.onnx'), str(CACHE/'voices-v1.0.bin'))
    audio, boundaries = [], []
    clock = 0.0
    for _, _, _, words in segments:
        samples, rate = kokoro.create(words, voice='af_heart', speed=1.0, lang='en-us')
        samples = np.concatenate([samples, np.zeros(round(rate*.35), dtype=np.float32)])
        duration = len(samples)/rate
        audio.append(samples); boundaries.append((clock, clock+duration)); clock += duration
    duration = max(30.0, clock)
    wave = np.concatenate(audio)
    if len(wave) < int(duration*rate):
        wave = np.pad(wave, (0, int(duration*rate)-len(wave)))
    wav = OUT / (day+'.wav'); sf.write(wav, wave, rate)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    fonts = {s: ImageFont.truetype(str(CACHE/'sora.ttf'), s) for s in (23,28,32,42,52)}
    arfont = ImageFont.truetype(str(CACHE/'arabic.ttf'), 38)
    gold=(212,175,55); ivory=(247,245,240); muted=(180,180,175)
    def wrapped(text,font,max_width):
        lines=[];current=''
        for word in text.split():
            candidate=(current+' '+word).strip()
            if current and font.getlength(candidate)>max_width:
                lines.append(current);current=word
            else:current=candidate
        if current:lines.append(current)
        return lines
    cards=[]
    for i,(label,text,ar,_) in enumerate(segments):
        im=Image.new('RGB',(720,1280),(11,11,11));d=ImageDraw.Draw(im)
        d.text((55,135),'ONE STEP',font=fonts[32],fill=gold)
        d.line((55,202,665,202),fill=(76,65,32),width=2)
        d.text((55,260),label,font=fonts[23],fill=gold)
        y=350
        for line in wrapped(text,fonts[52],610):
            d.text((55,y),line,font=fonts[52],fill=ivory);y+=76
        d.rectangle((55,y+32,145,y+37),fill=gold)
        # Arabic subtitles match the instructional message; keep within platform safe area.
        ary=880
        for arline in wrapped(ar,arfont,580):
            shaped=get_display(arabic_reshaper.reshape(arline))
            box=d.textbbox((0,0),shaped,font=arfont)
            d.text(((720-(box[2]-box[0]))/2,ary),shaped,font=arfont,fill=ivory);ary+=60
        d.text((55,1110),'0ne1stepuae@gmail.com',font=fonts[23],fill=muted)
        cards.append(im)
    tmp=OUT/(day+'.rendering.mp4')
    command=[ffmpeg,'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','720x1280','-r','24','-i','pipe:0','-i',str(wav),'-c:v','libx264','-preset','veryfast','-crf','24','-maxrate','1500k','-bufsize','3000k','-pix_fmt','yuv420p','-c:a','aac','-b:a','96k','-t',str(duration),'-movflags','+faststart',str(tmp)]
    proc=subprocess.Popen(command,stdin=subprocess.PIPE)
    try:
        for frame in range(math.ceil(duration*24)):
            t=frame/24
            idx=next((i for i,(a,b) in enumerate(boundaries) if a<=t<b),len(cards)-1)
            progress=(t-boundaries[idx][0])/max(.1,boundaries[idx][1]-boundaries[idx][0])
            im=cards[idx].copy();d=ImageDraw.Draw(im)
            # Moving workflow markers and progress bar make this an animated explainer.
            d.line((90,745,630,745),fill=(64,57,34),width=3)
            for dot in range(3):
                x=90+dot*270;d.ellipse((x-10,735,x+10,755),fill=gold if progress>dot/3 else (70,67,54))
            x=90+int(540*max(0,min(progress,1)));d.ellipse((x-8,737,x+8,753),fill=ivory)
            d.rectangle((55,1175,55+int(610*t/duration),1180),fill=gold)
            proc.stdin.write(im.tobytes())
    finally:
        proc.stdin.close()
    if proc.wait()!=0: raise RuntimeError('Video encoding failed')
    if tmp.stat().st_size>12000000: raise RuntimeError('Video exceeds free upload size bound')
    target.write_bytes(tmp.read_bytes());tmp.unlink()
    (OUT/(day+'.json')).write_text(json.dumps({'day':day,'title':title,'duration':duration,'format':'business-hack-motion-graphics','ugc':False,'bytes':target.stat().st_size}),encoding='utf-8')
    return target


def upload(path,day):
    receipt=OUT/(day+'.uploaded.json')
    if receipt.exists():return json.loads(receipt.read_text())
    key=os.environ.get('MARKETING_UPLOAD_KEY') or protect(CONFIG.read_bytes(),True).decode()
    req=urllib.request.Request(API,data=path.read_bytes(),method='POST',headers={'Content-Type':'video/mp4','x-marketing-upload-key':key})
    with urllib.request.urlopen(req,timeout=90) as response:
        result=json.load(response)
    receipt.write_text(json.dumps(result),encoding='utf-8');return result


def already_uploaded(day):
    key=os.environ.get('MARKETING_UPLOAD_KEY') or protect(CONFIG.read_bytes(),True).decode()
    req=urllib.request.Request(API.replace('mode=upload-video','mode=video-status'),data=b'{}',method='POST',headers={'Content-Type':'application/json','x-marketing-upload-key':key})
    try:
        with urllib.request.urlopen(req,timeout=20) as response:result=json.load(response)
        if result.get('day')==day and result.get('businessReady') is True:
            OUT.mkdir(parents=True,exist_ok=True)
            (OUT/(day+'.uploaded.json')).write_text(json.dumps({'day':day,'source':'existing-cloud-media'}),encoding='utf-8')
            return True
    except Exception:
        pass # Rendering remains the free fallback; upload admission is still day-idempotent.
    return False


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--setup',action='store_true');parser.add_argument('--render-only',action='store_true')
    args=parser.parse_args()
    if args.setup:setup();return
    day=datetime.now(timezone(timedelta(hours=4))).date().isoformat()
    if not args.render_only and already_uploaded(day):
        print(json.dumps({'day':day,'uploaded':True,'reused_cloud_media':True}));return
    path=render(day)
    if not args.render_only:upload(path,day)
    print(json.dumps({'day':day,'rendered':True,'uploaded':not args.render_only}))


if __name__=='__main__':main()
