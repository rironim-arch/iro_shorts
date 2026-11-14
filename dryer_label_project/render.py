"""Life Algorithm dryer-label short. One Charon take, real stock, aligned captions.
Run from this directory: python render.py. Requires GEMINI_API_KEY only for first run.
Never publishes to social accounts. Source footage is illustrative, not a shrinkage test.
"""
import os, re, json, wave, subprocess, math, difflib, shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent
os.chdir(ROOT)
OUT=ROOT/'output'; OUT.mkdir(exist_ok=True)
ASSETS=ROOT/'assets'; ASSETS.mkdir(exist_ok=True)
W,H,FPS=1080,1920,30
FONT='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
WHITE='#FAF9F6'; INK='#18221E'; GREEN='#146D55'; RED='#BD3F32'
SCRIPT=(ROOT/'script.txt').read_text().strip()
PHRASES=[
'건조기 돌렸더니\n옷이 줄었다고요?',
'넣기 전에,\n옷 안쪽 라벨부터 보세요.',
'네모 안 동그라미에 엑스.',
'이건 건조기\n사용 금지입니다.',
'저온 코스라도\n넣으면 안 돼요.',
'동그라미 안 점이 하나면',
'저온 건조 표시입니다.',
'그런데 면이라고\n무조건 괜찮은 건 아닙니다.',
'같은 소재라도\n가공과 혼방에 따라 달라서,',
'라벨이 기준이에요.',
'특히 울이나 실크는',
'수축과 손상에 주의하세요.',
'물세탁이 된다고',
'건조기도 되는 건 아닙니다.',
'표시가 지워졌다면\n제조사에 먼저 확인하세요.',
'옷 넣기 전,\n이 표시부터 확인하세요.',
'생활알고리즘.',
'유익했다면\n구독과 좋아요!']

def run(*args):
    subprocess.run([str(x) for x in args],check=True,stdout=subprocess.DEVNULL)
def ff(*args): run('ffmpeg','-y','-v','error',*args)
def norm(s):return ''.join(c for c in s if c.isalnum())
def probe(p):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(p)]))

def voice():
    original=ASSETS/'charon_original.wav'; final=ASSETS/'charon_125.wav'
    if not original.exists():
        from google import genai
        from google.genai import types
        client=genai.Client(api_key=os.environ['GEMINI_API_KEY'])
        r=client.models.generate_content(model='gemini-2.5-flash-preview-tts',
          contents='Read this Korean script once, as ONE continuous clear friendly Korean male narration. Keep the same voice throughout. Natural brisk conversational delivery. No added words, no music, no repeated phrases. The subscribe-and-like request appears ONLY at the end.\nSCRIPT:\n'+SCRIPT,
          config=types.GenerateContentConfig(response_modalities=['AUDIO'],speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name='Charon')))))
        inline=next(p.inline_data for p in r.candidates[0].content.parts if getattr(p,'inline_data',None) and p.inline_data.data)
        raw=inline.data
        if raw[:4]==b'RIFF':original.write_bytes(raw)
        else:
            rate=re.search(r'rate=(\d+)',inline.mime_type or '')
            with wave.open(str(original),'wb') as w:
                w.setnchannels(1);w.setsampwidth(2);w.setframerate(int(rate.group(1)) if rate else 24000);w.writeframes(raw)
    # Explicit continuing-series preference: apply the user's 1.25x once, then align.
    ff('-i',original,'-af','atempo=1.25','-ar','48000','-ac','1',final)
    return final

STOCK=[(8756891,'dryer',[(1920,1012,25),(960,506,25),(1280,674,25),(1920,1080,25)]),
       (7792705,'knit',[(1920,1080,25),(1280,720,25),(1080,1920,25),(720,1280,25),(1920,1080,30)]),
       (7855136,'fold',[(1920,1080,25),(1280,720,25)]),
       (8756886,'load',[(1080,2048,25),(720,1366,25),(540,1024,25),(1080,1920,25)])]

def get_stock(item):
    sid,name,variants=item; target=ASSETS/(name+'.mp4')
    if target.exists():return name
    session=requests.Session();session.headers['User-Agent']='Mozilla/5.0'
    urls=[f'https://videos.pexels.com/video-files/{sid}/{sid}-hd_{w}_{h}_{fps}fps.mp4' for w,h,fps in variants]
    urls += [f'https://videos.pexels.com/video-files/{sid}/{sid}-hd_{w}_{h}_{fps}fps.mp4' for w,h in [(1920,1080),(1080,1920),(1280,720),(720,1280),(960,540)] for fps in [25,30,24]]
    for u in dict.fromkeys(urls):
        try:
            r=session.get(u,timeout=(5,20),stream=True)
            if r.status_code!=200 or 'video' not in r.headers.get('Content-Type',''):r.close();continue
            raw=ASSETS/(name+'_raw.mp4')
            with raw.open('wb') as f:
                for b in r.iter_content(1024*1024):f.write(b)
            ff('-i',raw,'-t','14','-vf','scale=1080:1020:force_original_aspect_ratio=increase,crop=1080:1020,fps=30','-an','-c:v','libx264','-crf','19','-preset','fast',target)
            raw.unlink(); print('STOCK_READY',name,flush=True)
            return name
        except Exception:continue
    print('STOCK_UNAVAILABLE',name,flush=True);return None

def alignment(audio):
    cache=OUT/'asr.json'
    if cache.exists():words=json.loads(cache.read_text())
    else:
        from faster_whisper import WhisperModel
        model=WhisperModel('small',device='cpu',compute_type='int8',cpu_threads=4)
        segments,info=model.transcribe(str(audio),language='ko',beam_size=5,word_timestamps=True,vad_filter=True)
        words=[{'text':w.word,'start':w.start,'end':w.end,'probability':w.probability} for s in segments for w in s.words]
        cache.write_text(json.dumps(words,ensure_ascii=False,indent=2))
    heard=''.join(norm(w['text']) for w in words)
    expected=norm(''.join(PHRASES)); assert expected==norm(SCRIPT)
    ts=[]
    # Each recognized word carries a real interval. Character mapping only chooses
    # word ownership; no estimated individual-word caption timestamps are used.
    for word in words:ts.extend([(word['start'],word['end'])]*len(norm(word['text'])))
    sm=difflib.SequenceMatcher(None,expected,heard,autojunk=False)
    ratio=sm.ratio(); print('TRANSCRIPT_SIMILARITY',ratio,flush=True)
    if ratio<0.83:raise RuntimeError('Narration/transcript mismatch; review before rendering')
    mapping={}
    for block in sm.get_matching_blocks():
        for j in range(block.size):mapping[block.a+j]=block.b+j
    cues=[];offset=0
    for i,phrase in enumerate(PHRASES):
        n=len(norm(phrase)); indices=[mapping[k] for k in range(offset,offset+n) if k in mapping]
        if not indices:raise RuntimeError('Unaligned phrase '+phrase)
        cues.append({'start':ts[min(indices)][0],'end':ts[max(indices)][1],'text':phrase,'id':i})
        offset+=n
    for i in range(len(cues)-1):
        cues[i]['end']=min(cues[i+1]['start'],cues[i]['end']+0.1)
    dur=float(probe(audio)['format']['duration'])
    cues[-1]['end']=min(dur,cues[-1]['end']+0.15)
    for c in cues:
        if c['end']<=c['start']:raise RuntimeError('Caption interval collision')
    (OUT/'cues.json').write_text(json.dumps(cues,ensure_ascii=False,indent=2))
    def stamp(t):
        ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
    (OUT/'subtitles.srt').write_text('\n\n'.join(f'{i+1}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["text"]}' for i,c in enumerate(cues))+'\n')
    return cues,dur,ratio

def font(size):return ImageFont.truetype(FONT,size,index=1)
def text_center(draw,txt,y,size,fill=INK):
    f=font(size)
    for line in txt.split('\n'):
        b=draw.textbbox((0,0),line,font=f)
        if b[2]-b[0]>920:raise ValueError('Text too wide '+line)
        draw.text(((W-(b[2]-b[0]))/2-b[0],y-b[1]),line,font=f,fill=fill)
        y+=size*1.40

def symbol(draw,cx,cy,size,kind,progress=1):
    h=size/2; box=(cx-h,cy-h,cx+h,cy+h)
    draw.rectangle(box,outline=INK,width=13)
    draw.ellipse((cx-h+18,cy-h+18,cx+h-18,cy+h-18),outline=INK,width=13)
    if kind=='no':
        r=h+22
        draw.line((cx-r,cy-r,cx+r,cy+r),fill=RED,width=20)
        draw.line((cx+r,cy-r,cx-r,cy+r),fill=RED,width=20)
    if kind=='low':draw.ellipse((cx-23,cy-23,cx+23,cy+23),fill=INK)

def card(kind,phase=2):
    im=Image.new('RGB',(W,1020),WHITE);d=ImageDraw.Draw(im)
    if kind in ['no','low']:
        text_center(d,'옷 안쪽 라벨 · 기호 확대',90,42,GREEN)
        symbol(d,540,450,450,kind)
        if phase>=1:text_center(d,'건조기 사용 금지' if kind=='no' else '저온 건조',750,74,RED if kind=='no' else GREEN)
        if phase>=2:text_center(d,'저온 코스도 사용하지 않기' if kind=='no' else '옷과 기기의 안내 함께 확인',865,38)
    elif kind=='compare':
        text_center(d,'물세탁 가능',220,86)
        if phase>=1:
            text_center(d,'≠',405,130,RED)
            text_center(d,'건조기 사용 가능',625,86)
        if phase>=2:text_center(d,'건조 표시는 따로 확인',825,46,GREEN)
    elif kind=='recap':
        text_center(d,'넣기 전, 라벨 확인',70,64)
        symbol(d,315,430,240,'no');symbol(d,765,430,240,'low')
        for cx,txt in [(315,'사용 금지'),(765,'저온 건조')]:
            f=font(55);b=d.textbbox((0,0),txt,font=f);d.text((cx-(b[2]-b[0])/2,640),txt,font=f,fill=RED if cx==315 else GREEN)
        text_center(d,'소재 이름만 보고 결정하지 마세요',810,44)
    return im

def main():
    audio=voice(); print('VOICE_READY',flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:available=list(pool.map(get_stock,STOCK))
    if not all(x in available for x in ['knit','fold','load']):raise RuntimeError('Essential real footage unavailable')
    cues,dur,ratio=alignment(audio)
    footage={name:ASSETS/(name+'.mp4') for name in available if name}
    cards={k:card(k) for k in ['no','low','compare','recap']}
    card_states={(k,phase):card(k,phase) for k in cards for phase in range(3)}
    # Meaningful scenes follow actual phrase starts. Stock remains at 1x.
    groups=[(0,2,'knit' if 'knit' in footage else 'fold'),(2,5,'no'),(5,7,'low'),(7,10,'fold'),(10,12,'knit' if 'knit' in footage else 'fold'),(12,14,'compare'),(14,15,'load' if 'load' in footage else 'dryer'),(15,18,'recap')]
    scenes=[]
    for lo,hi,kind in groups:scenes.append((0 if lo==0 else cues[lo]['start'],cues[hi]['start'] if hi<len(cues) else dur,kind))
    base=Image.new('RGB',(W,H),WHITE);d=ImageDraw.Draw(base)
    text_center(d,'생활알고리즘',55,54,GREEN)
    text_center(d,'건조기 넣기 전\n이 표시부터!',145,83)
    d.rectangle((0,365,W,1375),fill='#E9ECE7')
    # Main imagery fills 1080x1020. Captions stay inside x=100..980,
    # y=1430..1630, leaving the bottom UI area clear.
    captions={}
    for c in cues:
        layer=Image.new('RGBA',(W,340),(0,0,0,0));ld=ImageDraw.Draw(layer)
        text_center(ld,c['text'],35,62,RED if c['id'] in [3,4,13] else INK)
        captions[c['id']]=layer
    total=math.ceil(dur*FPS)
    picture=OUT/'picture.mp4'
    proc=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-crf','19','-preset','fast','-pix_fmt','yuv420p','-movflags','+faststart',str(picture)],stdin=subprocess.PIPE)
    preview_times=[0.6, cues[3]['start']+0.3,cues[6]['start']+0.3,cues[9]['start']+0.3,cues[13]['start']+0.3,cues[-1]['start']+0.3]
    previews={round(t*FPS):i for i,t in enumerate(preview_times)}
    reader=None;previous_scene=None
    for frame in range(total):
        t=frame/FPS;im=base.copy()
        if t<cues[1]['start']:
            hd=ImageDraw.Draw(im);hd.rectangle((0,125,W,360),fill=WHITE)
            text_center(hd,'멀쩡하던 옷이\n왜 줄었지?',145,83)
        scene=next(s for s in scenes if s[0]<=t<s[1]) if t<dur else scenes[-1]
        start,end,kind=scene
        if scene!=previous_scene:
            if reader:
                reader.stdout.close();reader.terminate();reader.wait();reader=None
            if kind in footage:
                source_offset=4 if start>=cues[10]['start'] and kind=='knit' else 0
                if float(probe(footage[kind])['format']['duration'])-source_offset<end-start:
                    source_offset=0
                if float(probe(footage[kind])['format']['duration'])-source_offset<end-start:
                    raise RuntimeError('B-roll shorter than scene; no looping')
                reader=subprocess.Popen(['ffmpeg','-v','error','-ss',str(source_offset),'-i',str(footage[kind]),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
            previous_scene=scene
        if kind in cards:
            phase=2
            if kind=='no':phase=0 if t<cues[3]['start'] else (1 if t<cues[4]['start'] else 2)
            elif kind=='low':phase=0 if t<cues[6]['start'] else 2
            elif kind=='compare':phase=0 if t<cues[13]['start'] else 2
            visual=card_states[kind,phase]
        else:
            raw=reader.stdout.read(1020*W*3)
            if len(raw)!=1020*W*3:raise RuntimeError('B-roll decode ended early')
            visual=Image.frombytes('RGB',(W,1020),raw)
        im.paste(visual,(0,365))
        c=next((c for c in cues if c['start']<=t<c['end']),None)
        if c:im.paste(captions[c['id']],(0,1420),captions[c['id']])
        if kind not in cards:
            dd=ImageDraw.Draw(im);dd.rounded_rectangle((28,1300,210,1355),radius=12,fill=WHITE);dd.text((47,1304),'자료 화면',font=font(31),fill=INK)
        if frame in previews:im.resize((360,640)).save(OUT/f'preview_{previews[frame]:02}.jpg')
        proc.stdin.write(im.tobytes())
    proc.stdin.close()
    if reader:reader.stdout.close();reader.terminate();reader.wait()
    if proc.wait()!=0:raise RuntimeError('Video encode failed')
    ff('-i',picture,'-i',audio,'-map','0:v:0','-map','1:a:0','-c:v','copy','-af','loudnorm=I=-16:TP=-1.5:LRA=7','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',OUT/'dryer_label_short.mp4')
    picture.unlink()
    ff('-i',OUT/'dryer_label_short.mp4','-f','null','-')
    meta={'duration':dur,'size':[W,H],'fps':FPS,'voice':'Gemini Charon, one continuous take','user_requested_speed':1.25,'transcript_similarity':ratio,'listening_review':'not_performed','visual_review':'pending','scenes':scenes,'sources':['https://www.ginetex.net/GB/labelling/care-symbols.asp','https://www.lge.co.kr/support/solutions-20151827436317'],'stock':[f'https://www.pexels.com/video/{sid}/' for sid,_,_ in STOCK],'stock_license':'https://www.pexels.com/license/'}
    (OUT/'quality.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
    shutil.copy(ROOT/'script.txt',OUT/'script.txt')
    print('COMPLETE',dur,flush=True)

if __name__=='__main__':main()
