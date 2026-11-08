"""Create a daily fictional AI spokesperson script and free local speech; no testimonial."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[2]

def main():
    import numpy as np
    import soundfile as sf
    from kokoro_onnx import Kokoro
    from daily_video import TIPS
    day=datetime.now(timezone(timedelta(hours=4))).date().isoformat()
    ordinal=(datetime.fromisoformat(day)-datetime(1970,1,1)).days
    title,steps,arabic=TIPS[ordinal%len(TIPS)]
    parts=[
      ('Here is a practical idea for organising your business enquiries. '+title+'.','فكرة عملية لتنظيم استفسارات العملاء في شركتك.'),
      *[(s+' Keep this step clear and useful for your team.',a) for s,a in zip(steps,arabic)],
      ('Start with one workflow and check it with a real enquiry before expanding it. The process should match how your team actually works.','ابدأ بعملية واحدة واختبرها قبل توسيع الأتمتة.'),
      ('At One Step, we build websites, CRM systems and enquiry automations. Message One Step to discuss a practical place to start for your business.','ون ستيب تطور المواقع وأنظمة إدارة العملاء وأتمتة الاستفسارات. راسلنا لمناقشة احتياجات شركتك.')]
    out=ROOT/'state/daily-marketing';out.mkdir(parents=True,exist_ok=True)
    if (out/(day+'-ugc.wav')).exists() and (out/(day+'-ugc.json')).exists():return
    cache=ROOT/'state/marketing-cache'
    model=Kokoro(str(cache/'kokoro-v1.0.int8.onnx'),str(cache/'voices-v1.0.bin'))
    audio=[];cues=[];clock=0.0
    for words,ar in parts:
        samples,rate=model.create(words,voice='am_michael',speed=.9,lang='en-us')
        samples=np.concatenate([samples,np.zeros(round(rate*.25),dtype=np.float32)])
        end=clock+len(samples)/rate;cues.append({'start':clock,'end':end,'en':words,'ar':ar});clock=end;audio.append(samples)
    if clock<30 or clock>90:raise RuntimeError('UGC speech must be between 30 and 90 seconds')
    sf.write(out/(day+'-ugc.wav'),np.concatenate(audio),rate)
    (out/(day+'-ugc.json')).write_text(json.dumps({'day':day,'duration':clock,'title':title,'cues':cues,'fictional_ai_presenter':True},ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'day':day,'ugc_speech_seconds':clock}))

if __name__=='__main__':main()
