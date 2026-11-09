"""Continuous, restrained speech-aware head motion over the full original audio."""
import argparse
from pathlib import Path
import runpy
import sys


def smooth_curve(values,frames,positions=None):
    import numpy as np
    positions=np.linspace(0,frames-1,len(values)) if positions is None else positions
    out=np.zeros(frames)
    for i in range(len(values)-1):
        left=int(round(positions[i]));right=int(round(positions[i+1]))
        t=np.linspace(0,1,right-left+1);ease=t*t*(3-2*t)
        out[left:right+1]=values[i]+(values[i+1]-values[i])*ease
    return out


def profile(audio_path):
    import numpy as np
    import soundfile as sf
    from scipy.ndimage import gaussian_filter1d
    samples,rate=sf.read(audio_path)
    if samples.ndim>1:samples=samples.mean(axis=1)
    frames=int(len(samples)/rate*25);width=rate/25
    energy=np.array([np.sqrt(np.mean(samples[int(i*width):max(int((i+1)*width),int(i*width)+1)]**2)+1e-10) for i in range(frames)])
    energy=gaussian_filter1d(energy,2.5);energy/=max(float(np.percentile(energy,95)),1e-5)
    # Irregular timing and amplitudes avoid metronomic left/right sway.
    rng=np.random.RandomState(17);positions=[0]
    while positions[-1]<frames-1:
        remaining=frames-1-positions[-1]
        if remaining<43 and len(positions)>1:
            positions[-1]=frames-1
            break
        positions.append(min(frames-1,positions[-1]+round(rng.uniform(1.7,3.1)*25)))
    yaw=smooth_curve([0]+rng.uniform(-3.4,3.4,len(positions)-1).tolist(),frames,positions)
    pitch=smooth_curve([0]+rng.uniform(-.6,.6,len(positions)-1).tolist(),frames,positions)-1.8*gaussian_filter1d(np.clip(energy,0,1),4)
    pitch-=pitch[0]
    roll=smooth_curve([0]+rng.uniform(-.6,.6,len(positions)-1).tolist(),frames,positions)
    return np.stack([yaw,pitch,roll],axis=1)


def main():
    p=argparse.ArgumentParser(add_help=False);p.add_argument('--motion-audio',required=True);p.add_argument('--motion-offset',type=float,default=0)
    args,remaining=p.parse_known_args();import numpy as np
    import torch
    sys.path.insert(0,str(Path.cwd()))
    import src.generate_facerender_batch as batch_module
    import src.generate_batch as audio_module
    import src.facerender.modules.make_animation as animation
    full=profile(args.motion_audio);offset=round(args.motion_offset*25)
    original_batch=batch_module.get_facerender_data
    original_transform=animation.keypoint_transformation
    base={}

    def render_data(*a,**kw):
        data=original_batch(*a,**kw);n=data['frame_num'];batch_size=data['source_image'].shape[0]
        indices=np.clip(np.arange(offset,offset+n),0,len(full)-1)
        for j,name in enumerate(('yaw_c_seq','pitch_c_seq','roll_c_seq')):
            values=full[indices,j]
            if n%batch_size:values=np.pad(values,(0,batch_size-n%batch_size),mode='edge')
            data[name]=torch.tensor(values.reshape(batch_size,-1),dtype=torch.float32)
        return data

    def transform(kp,he,wo_exp=False):
        if not base:
            for name in ('yaw','pitch','roll'):base[name]=animation.headpose_pred_to_degree(he[name]).clone()
            base['t']=he['t'].clone()
        if 'yaw_in' in he:
            he=dict(he)
            for name in ('yaw','pitch','roll'):he[name+'_in']=base[name]+he[name+'_in']
            # Preserve source position while damping the learned vertical bobble.
            he['t']=base['t']+.25*(he['t']-base['t'])
        return original_transform(kp,he,wo_exp=wo_exp)

    def blink(n):
        ratio=np.zeros((n,1))
        for second in (2.6,6.4,10.9,15.2,19.0,23.6,28.1,32.4,36.8,41.5,45.7,50.3,55.0,59.4,64.0,68.7,73.2,77.8,82.1,86.5):
            at=round(second*25)-offset
            for j,v in enumerate((.4,.85,1,.75,.3)):
                if 0<=at+j<n:ratio[at+j,0]=v
        return ratio

    batch_module.get_facerender_data=render_data
    animation.keypoint_transformation=transform
    audio_module.generate_blink_seq_randomly=blink
    sys.argv=['inference.py']+remaining
    runpy.run_path(str(Path('inference.py').resolve()),run_name='__main__')


if __name__=='__main__':main()
