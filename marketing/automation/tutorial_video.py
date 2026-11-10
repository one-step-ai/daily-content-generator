"""Black/gold animated screen tutorial with an original cartoon instructor."""
import argparse
import json
import math
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
W, H, FPS = 720, 1280, 24
BLACK, GOLD, WHITE = (8, 9, 10), (212, 175, 55), (247, 245, 240)


def render(metadata, audio, target, offset=0, seconds=None):
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    import numpy as np
    import soundfile as sf
    import imageio_ffmpeg
    import arabic_reshaper
    from bidi.algorithm import get_display
    from ugc_style import caption_chunks, active_cue

    data = json.loads(Path(metadata).read_text(encoding='utf-8'))
    duration = min(data['duration']-offset, seconds or data['duration'])
    if duration <= 0 or len(data['cues']) != 6:
        raise ValueError('A valid six-section script timeline is required')
    samples, rate = sf.read(audio)
    if samples.ndim > 1:
        samples = samples.mean(axis=1)
    if abs(len(samples)/rate-data['duration']) > .2:
        raise ValueError('Narration and caption timelines differ')
    energy = []
    for frame in range(math.ceil(data['duration']*FPS)):
        chunk = samples[int(frame*rate/FPS):int((frame+1)*rate/FPS)]
        energy.append(float(np.sqrt(np.mean(chunk**2)+1e-10)) if len(chunk) else 0)
    peak = max(float(np.percentile(energy, 85)), 1e-4)
    fonts = {}
    cache = ROOT/'state/marketing-cache'
    for size in (16, 18, 20, 22, 24, 26, 28, 30, 32, 36, 42, 48, 54):
        fonts[size] = ImageFont.truetype(str(cache/'sora.ttf'), size)
        try:
            fonts[size].set_variation_by_axes([650 if size >= 36 else 500])
        except (OSError, ValueError):
            pass
    arfont = ImageFont.truetype(str(cache/'arabic.ttf'), 43,
                               layout_engine=ImageFont.Layout.BASIC)
    base = Image.open(ROOT/'marketing/automation/assets/cartoon-instructor.png').convert('RGBA')
    talking = Image.open(ROOT/'marketing/automation/assets/cartoon-instructor-talking.png').convert('RGBA')
    if talking.size != base.size:
        talking = talking.resize(base.size, Image.Resampling.LANCZOS)
    # Only the generated mouth keyframe changes; identity and pointing pose stay fixed.
    mouth_box = (507, 295, 640, 358)
    mask = Image.new('L', (mouth_box[2]-mouth_box[0], mouth_box[3]-mouth_box[1]))
    ImageDraw.Draw(mask).rounded_rectangle((5, 5, mask.width-5, mask.height-5), radius=12, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(4))
    open_base = base.copy()
    patch = Image.composite(talking.crop(mouth_box), base.crop(mouth_box), mask)
    open_base.paste(patch, mouth_box)
    sprites = [base.resize((276, 252), Image.Resampling.LANCZOS),
               open_base.resize((276, 252), Image.Resampling.LANCZOS)]
    bg = Image.new('RGB', (W, H), BLACK)
    d = ImageDraw.Draw(bg)
    for x in range(24, W, 32):
        for y in range(24, H, 32):
            d.ellipse((x, y, x+1, y+1), fill=(33, 29, 18))

    def ease(x):
        x = max(0, min(1, x))
        return 1-(1-x)**3

    def text(d, xy, value, size=24, fill=WHITE):
        d.text(xy, value, font=fonts[size], fill=fill)

    def window(d, box, title):
        x1, y1, x2, y2 = box
        d.rounded_rectangle((x1+7, y1+9, x2+7, y2+9), radius=17, fill=(0, 0, 0))
        d.rounded_rectangle(box, radius=17, fill=(23, 25, 25), outline=(94, 80, 37), width=2)
        d.line((x1+2, y1+48, x2-2, y1+48), fill=(62, 59, 47), width=1)
        for j in range(3):
            d.ellipse((x1+16+j*14, y1+18, x1+22+j*14, y1+24),
                      fill=GOLD if j == 0 else (86, 84, 73))
        text(d, (x1+68, y1+12), title, 16, (209, 205, 185))

    def cursor(d, x, y, click=False):
        if click:
            d.ellipse((x-22, y-22, x+22, y+22), outline=GOLD, width=2)
        d.polygon([(x, y), (x+10, y+30), (x+16, y+16), (x+30, y+11)], fill=GOLD)

    labels = ['THE MISSING NEXT STEP', '01  CAPTURE THE ENQUIRY', '02  ASSIGN AN OWNER',
              '03  UPDATE ON A REPLY', '04  TEST THE WORKFLOW', 'MAKE IT WORK FOR YOUR TEAM']
    titles = [('Every enquiry needs', 'a clear next step.'),
              ('Build one', 'shared record.'), ('Give the next step', 'a clear owner.'),
              ('A new reply?', 'Update the workflow.'), ('Test one enquiry.', 'Then expand.'),
              ('Websites. CRM.', 'Enquiry automation.')]
    notebook = data.get('daily_tutorial') is True
    steps = data.get('steps', [])

    def wrap(value, size, width):
        result, line = [], ''
        for word in value.split():
            trial = (line+' '+word).strip()
            if line and fonts[size].getlength(trial) > width:
                result.append(line)
                line = word
            else:
                line = trial
        if line:
            result.append(line)
        return result

    if notebook:
        if len(steps) != 3:
            raise ValueError('Daily tutorial requires three reviewed instructions')
        labels = ['TODAY’S BUSINESS PLAYBOOK', '01  FIRST STEP', '02  NEXT STEP',
                  '03  PUT IT INTO PRACTICE', '04  TEST BEFORE EXPANDING',
                  'MAKE IT WORK FOR YOUR TEAM']
        titles = [data['title'], *steps, 'Start small. Test the result.',
                  'Websites. CRM. Enquiry automation.']

    def canvas_at(t):
        index = active_cue(data['cues'], t)
        cue = data['cues'][index]
        p = max(0, min(1, (t-cue['start'])/(cue['end']-cue['start'])))
        im = bg.copy()
        d = ImageDraw.Draw(im)
        text(d, (42, 47), 'ONE STEP', 28, GOLD)
        text(d, (489, 56), 'BUSINESS PLAYBOOK', 16, (160, 155, 135))
        d.line((42, 104, 678, 104), fill=(86, 73, 33), width=2)
        text(d, (43, 135), labels[index], 18, (174, 165, 131))
        heading = wrap(titles[index], 48, 635) if notebook else titles[index]
        heading_size = 48
        if notebook:
            for candidate_size in (48, 42, 36, 32):
                heading_size = candidate_size
                heading = wrap(titles[index], heading_size, 635)
                if len(heading) <= 2:
                    break
        for j, line in enumerate(heading):
            text(d, (41, 181+j*65), line, heading_size, GOLD if j else WHITE)
        if notebook and index <= 3:
            window(d, (38, 350, 677, 920), 'WORKFLOW NOTEBOOK / ILLUSTRATIVE DEMO')
            text(d, (65, 422), 'THREE PRACTICAL STEPS', 18, GOLD)
            active = index-1
            for j, instruction in enumerate(steps):
                yy = 480+j*132
                selected = j == active or index == 0 and j == min(2, int(p*3))
                if selected:
                    d.rectangle((59, yy-9, 656, yy+103), fill=(42, 39, 28))
                    d.rectangle((59, yy-9, 63, yy+103), fill=GOLD)
                text(d, (77, yy+4), f'{j+1:02}', 20, GOLD)
                visible = instruction
                if j == active:
                    visible = instruction[:round(len(instruction)*ease(p/.6))]
                for row, line in enumerate(wrap(visible, 24, 512)):
                    text(d, (124, yy+row*35), line, 24,
                         WHITE if selected else (157, 155, 142))
            cursor(d, 615, 516+max(0, active)*132, index > 0 and .2 < p < .7)
        elif index in (0, 1, 3):
            window(d, (38, 352, 383, 716), 'ENQUIRY INBOX')
            text(d, (59, 419), 'New reply' if index == 3 else 'Website enquiry', 22)
            text(d, (59, 463), 'Please send us' if index == 3 else 'Can you help us', 22, (204, 204, 194))
            text(d, (59, 497), 'the next steps.' if index == 3 else 'organise enquiries?', 22, (204, 204, 194))
            d.rounded_rectangle((58, 561, 338, 604), radius=11, fill=(49, 46, 32))
            text(d, (72, 572), 'Demo conversation', 18, GOLD)
            window(d, (238, 639 if index == 0 else 565, 676, 920),
                   'NEXT ACTION' if index == 0 else 'CRM RECORD')
            y = 713 if index == 0 else 642
            if index == 0:
                text(d, (259, y), 'Reply sent', 26)
                text(d, (259, y+61), 'Owner: unassigned', 22, GOLD)
                text(d, (259, y+108), 'Next action: missing', 22, GOLD)
                cursor(d, 579, y+118, p > .58)
            elif index == 1:
                values = [('NEED', 'Organise customer enquiries'),
                          ('SOURCE', 'Website contact form'),
                          ('LATEST MESSAGE', 'Conversation saved')]
                for j, (key, value) in enumerate(values):
                    yy = y+j*87
                    text(d, (259, yy), key, 16, (161, 158, 140))
                    count = round(len(value)*ease((p-j*.2)/.27))
                    text(d, (259, yy+27), value[:count], 20)
                cursor(d, 614, 852, .35 < p < .8)
            else:
                text(d, (259, y), 'New reply received', 24, GOLD)
                text(d, (259, y+63), 'Record updated', 24)
                if p > .35:
                    text(d, (259, y+124), 'Review + set next action', 20)
                cursor(d, 598, y+133, p > .4)
        elif index == 2:
            window(d, (38, 350, 677, 920), 'FOLLOW-UP WORKFLOW / DEMO')
            for j, (label, value) in enumerate([('ENQUIRY', 'CRM and enquiry handling'),
                                               ('OWNER', 'Alex (demo)'),
                                               ('NEXT ACTION', 'Clarify requirements'),
                                               ('DUE', 'Next working day (demo)')]):
                yy = 436+j*105
                text(d, (64, yy), label, 18, (165, 160, 138))
                d.rounded_rectangle((241, yy-6, 648, yy+51), radius=10, fill=(39, 40, 36),
                                    outline=GOLD if j == min(3, int(p*5)) else (62, 63, 54))
                if j == 0 or p > .08+(j-1)*.2:
                    text(d, (257, yy+8), value, 22)
            d.rounded_rectangle((438, 846, 648, 893), radius=11, fill=GOLD)
            text(d, (456, 859), 'SAVED' if p > .9 else 'SAVE FOLLOW-UP', 18, BLACK)
            cursor(d, 587, 865 if p > .78 else 552+int(190*ease(p)), .78 < p < .95)
        elif index == 4:
            window(d, (38, 350, 677, 920), 'WORKFLOW CHECK / DEMO')
            checks = (['Try one real enquiry', 'Check the result', 'Adjust the workflow',
                       'Expand after testing'] if notebook else
                      ['Capture the enquiry', 'Check the assigned owner',
                       'Review the next action', 'Test before expanding'])
            for j, value in enumerate(checks):
                yy = 450+j*100
                d.rounded_rectangle((66, yy, 110, yy+43), radius=10, outline=(122, 110, 71), width=2)
                if p > .07+j*.2:
                    d.line((76, yy+23, 87, yy+32, 102, yy+11), fill=GOLD, width=4)
                text(d, (135, yy+6), value, 26)
        else:
            window(d, (38, 350, 677, 920), 'ONE STEP / CONNECTED WORKFLOWS')
            for j, value in enumerate(['Website enquiry', 'Shared CRM record', 'Clear follow-up']):
                yy = 445+j*122
                active = j == min(2, int(p*4))
                d.rounded_rectangle((95, yy, 620, yy+73), radius=14,
                                    fill=GOLD if active else (40, 41, 36))
                text(d, (126, yy+19), value, 28, BLACK if active else WHITE)
                if j < 2:
                    d.line((360, yy+79, 360, yy+112), fill=GOLD, width=3)
                    d.polygon([(360, yy+112), (351, yy+101), (369, yy+101)], fill=GOLD)
            text(d, (165, 859), 'MESSAGE ONE STEP', 26, GOLD)
        text(d, (41, 938), 'ILLUSTRATIVE DEMO  /  FICTIONAL DATA', 16, (133, 129, 111))
        level = min(1, energy[min(len(energy)-1, int(t*FPS))]/peak)
        sprite = sprites[1 if level > .24 else 0]
        # Subtle motion keeps the instructor engaged while his pointer faces the screen.
        angle = math.sin(t*1.6)*.7 + level*.6
        character = sprite.rotate(angle, Image.Resampling.BICUBIC, expand=False)
        im.paste(character, (16, 984+round(math.sin(t*2)*2)), character)
        d = ImageDraw.Draw(im)
        chunks = caption_chunks(cue['ar'], max_words=4)
        ar = chunks[min(len(chunks)-1, int(p*len(chunks)))]
        arlines, line = [], ''
        for word in ar.split():
            candidate = (line+' '+word).strip()
            if line and arfont.getlength(get_display(arabic_reshaper.reshape(candidate))) > 386:
                arlines.append(line)
                line = word
            else:
                line = candidate
        if line:
            arlines.append(line)
        if len(arlines) > 3:
            raise ValueError('Subtitle exceeds the cartoon tutorial safe area')
        for row, line in enumerate(arlines):
            shaped = get_display(arabic_reshaper.reshape(line))
            width = arfont.getlength(shaped)
            d.text((307+(386-width)/2, 1030+row*56), shaped, font=arfont, fill=WHITE)
        d.line((308, 1216, 677, 1216), fill=(77, 65, 29), width=2)
        text(d, (310, 1230), '0ne1stepuae@gmail.com', 18, GOLD)
        return im

    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    proc = subprocess.Popen([ff, '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                             '-s', f'{W}x{H}', '-r', str(FPS), '-i', 'pipe:0', '-ss', str(offset),
                             '-i', str(audio), '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'libx264',
                             '-preset', 'fast', '-crf', '19', '-maxrate', '1500k', '-bufsize', '3000k',
                             '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', '-t', str(duration),
                             '-movflags', '+faststart', str(target)], stdin=subprocess.PIPE)
    try:
        for frame in range(math.ceil(duration*FPS)):
            im = canvas_at(offset+frame/FPS)
            proc.stdin.write(im.tobytes())
    finally:
        proc.stdin.close()
        status = proc.wait()
    if status:
        raise RuntimeError('Tutorial export failed')
    if target.stat().st_size > 12000000:
        raise RuntimeError('Tutorial exceeds free media size limit')
    return {'path': str(target), 'seconds': duration, 'bytes': target.stat().st_size}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--metadata', required=True)
    p.add_argument('--audio', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--offset', type=float, default=0)
    p.add_argument('--seconds', type=float)
    a = p.parse_args()
    print(json.dumps(render(a.metadata, a.audio, a.output, a.offset, a.seconds)))
