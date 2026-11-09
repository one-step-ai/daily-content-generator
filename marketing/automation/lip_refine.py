"""A separate audio-conditioned MuseTalk pass confined to the mouth region."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--audio',required=True)
    p.add_argument('--output',required=True);p.add_argument('--seconds',type=float)
    a=p.parse_args()
    import cv2
    import numpy as np
    import torch
    from transformers import WhisperModel
    torch.set_num_threads(4);torch.manual_seed(17)
    muse=ROOT/'state/MuseTalk';sys.path.insert(0,str(muse))
    from musetalk.models.vae import VAE
    from musetalk.models.unet import UNet,PositionalEncoding
    from musetalk.utils.audio_processor import AudioProcessor
    device=torch.device('cpu');models=muse/'models'
    vae=VAE(model_path=str(models/'sd-vae'))
    net=UNet(unet_config=str(models/'musetalkV15/musetalk.json'),model_path=str(models/'musetalkV15/unet.pth'),device=device)
    vae.vae.eval();net.model.eval();pe=PositionalEncoding(d_model=384).eval()
    whisper=WhisperModel.from_pretrained(str(models/'whisper'),local_files_only=True).eval()
    processor=AudioProcessor(feature_extractor_path=str(models/'whisper'))
    source=Path(a.source).resolve();audio=Path(a.audio).resolve();target=Path(a.output).resolve();target.parent.mkdir(parents=True,exist_ok=True)
    cap=cv2.VideoCapture(str(source));fps=cap.get(cv2.CAP_PROP_FPS)
    if abs(fps-25)>.01:raise ValueError('Lip refinement requires the exact25fps source timeline')
    w=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH));h=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    features,length=processor.get_audio_feature(str(audio))
    with torch.inference_mode():chunks=processor.get_whisper_chunk(features,device,torch.float32,whisper,length,fps=25)
    limit=min(len(chunks),int(round(a.seconds*25)) if a.seconds else len(chunks))
    classifier=cv2.CascadeClassifier(cv2.data.haarcascades+'haarcascade_frontalface_default.xml')
    previous=None
    # Only the lower face is replaced, preserving native512 eyes, skin and head motion.
    mask=np.zeros((256,256),np.float32)
    cv2.ellipse(mask,(128,168),(76,33),0,0,360,1,-1)
    mask=cv2.GaussianBlur(mask,(15,15),4)[...,None]
    silent=target.with_name(target.stem+'.silent.mp4')
    enc=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','bgr24','-s',f'{w}x{h}',
        '-r','25','-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','18','-maxrate','1500k','-bufsize','3000k','-pix_fmt','yuv420p',str(silent)],stdin=subprocess.PIPE)
    started=time.monotonic();completed=0
    try:
        with torch.inference_mode():
            for i in range(limit):
                ok,frame=cap.read()
                if not ok:raise RuntimeError('Source video ended before the original speech')
                if i%5==0 or previous is None:
                    gray=cv2.cvtColor(frame[:int(h*.69)],cv2.COLOR_BGR2GRAY)
                    faces=classifier.detectMultiScale(gray,scaleFactor=1.08,minNeighbors=5,minSize=(100,100))
                    if len(faces):
                        x,y,fw,fh=max(faces,key=lambda b:b[2]*b[3])
                        # Put the mid-crop masking boundary at the nose, matching
                        # MuseTalk's landmark-based training crop for this presenter.
                        box=np.array([x+.06*fw,y+.20*fh,x+.94*fw,y+1.08*fh],dtype=float)
                        previous=box if previous is None else .22*box+.78*previous
                    elif previous is None:raise RuntimeError('No reliable frontal face detected')
                x1,y1,x2,y2=np.rint(previous).astype(int)
                x1=max(0,x1);y1=max(0,y1);x2=min(w,x2);y2=min(h,y2)
                crop=cv2.resize(frame[y1:y2,x1:x2],(256,256),interpolation=cv2.INTER_LANCZOS4)
                # Posterior means remove per-frame sampling noise from the VAE.
                masked=vae.preprocess_img(crop,half_mask=True);reference=vae.preprocess_img(crop,half_mask=False)
                latent=torch.cat([vae.scaling_factor*vae.vae.encode(masked).latent_dist.mode(),
                                  vae.scaling_factor*vae.vae.encode(reference).latent_dist.mode()],dim=1)
                prediction=net.model(latent,torch.tensor([0]),encoder_hidden_states=pe(chunks[i:i+1])).sample
                generated=vae.decode_latents(prediction)[0].astype(np.float32)
                outer=(mask[...,0]>.05)&(mask[...,0]<.25)
                adjustment=np.clip(crop[outer].mean(axis=0)-generated[outer].mean(axis=0),-16,16)
                generated=np.clip(generated+adjustment,0,255)
                generated=np.clip(generated+.45*(generated-cv2.GaussianBlur(generated,(0,0),.65)),0,255)
                full_generated=cv2.resize(generated,(x2-x1,y2-y1),interpolation=cv2.INTER_LANCZOS4)
                full_mask=cv2.resize(mask[...,0],(x2-x1,y2-y1))[...,None]
                original=frame[y1:y2,x1:x2].astype(np.float32)
                frame[y1:y2,x1:x2]=(full_generated*full_mask+original*(1-full_mask)).clip(0,255).astype(np.uint8)
                enc.stdin.write(frame.tobytes());completed+=1
                if completed%10==0:print(json.dumps({'lip_frames':completed,'total':limit,'seconds':round(time.monotonic()-started,1)}),flush=True)
    finally:
        cap.release();enc.stdin.close();status=enc.wait()
    if status or completed!=limit:raise RuntimeError('Incomplete lip refinement')
    subprocess.run(['ffmpeg','-y','-v','error','-i',str(silent),'-i',str(audio),'-map','0:v:0','-map','1:a:0',
        '-t',str(completed/25),'-c:v','copy','-c:a','aac','-b:a','128k','-movflags','+faststart',str(target)],check=True)
    subprocess.run(['ffmpeg','-v','error','-i',str(target),'-f','null','-'],check=True)
    print(json.dumps({'lip_refinement_complete':True,'frames':completed,'path':str(target)}),flush=True)


if __name__=='__main__':main()
