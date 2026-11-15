#!/usr/bin/env python3
# Somin 8-chapter long-form production: one female Kore narration, speech-derived subtitles, 1080p MP4.
# Output in somin_2026_output. Fictionalized characters; no user personal data or real names.
import os, re, io, json, time, math, wave, base64, difflib, shutil, subprocess, traceback, unicodedata
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
from google import genai
from google.genai import types

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"somin_2026_output"
AUDIO=OUT/"audio_chunks"; SLIDES=OUT/"slides"
for p in (OUT,AUDIO,SLIDES):p.mkdir(parents=True,exist_ok=True)
STORY=json.loads((ROOT/"somin_longform_story_2026.json").read_text(encoding="utf8"))
SPEED=1.25
RATE=24000
CAP=500
FF=shutil.which("ffmpeg") or "ffmpeg"
KEY=os.environ.get("GEMINI_API_KEY","")
if not KEY:raise RuntimeError("GEMINI_API_KEY secret is absent. Never replace Kore with another voice.")
client=genai.Client(api_key=KEY)
def run(cmd,timeout=3600):
    subprocess.run(cmd,check=True,timeout=timeout)
def wavduration(path):
    with wave.open(str(path),"rb") as w:return w.getnframes()/w.getframerate()
def norm(s):
    return re.sub(r"[^가-힣A-Za-z0-9]","",unicodedata.normalize("NFKC",s)).lower()
def split_chunks(s,cap=CAP):
    text=re.sub(r"\s+"," ",s).strip()
    sentences=re.split(r"(?<=[.!?])\s+",text)
    out=[];cur=""
    for sentence in sentences:
        if not sentence:continue
        if len(sentence)>cap:
            if cur:out.append(cur.strip());cur=""
            while len(sentence)>cap:
                at=sentence.rfind(" ",0,cap)
                if at<cap//2:at=cap
                out.append(sentence[:at].strip())
                sentence=sentence[at:].strip()
        if sentence:
            if cur and len(cur)+len(sentence)+1>cap:
                out.append(cur.strip());cur=""
            cur=(cur+" "+sentence).strip()
    if cur:out.append(cur)
    assert "".join(norm(x) for x in out)==norm(text), "Story text split changed content"
    return out
def synth(chunk, index):
    final=AUDIO/f"chunk_{index:03d}_125.wav"
    if final.exists() and wavduration(final)>2:return final
    prompt=("한국어 오디오북 내레이션. 성우는 49세 한국 여성 소민 한 사람입니다. "
       "처음부터 끝까지 똑같은 성우의 목소리로, 일정한 음높이와 말투로, 조용하고 따뜻하게 읽으세요. "
       "중요: 직접 인용된 엄마, 아빠, 동생, 아이의 대사도 다른 사람의 음성으로 연기하거나 성별/연령/목소리를 바꾸지 마세요. "
       "성우 한 사람의 담백한 낭독만 허용합니다. 우는 연기, 소리 지르기, 캐릭터 목소리, 속삭이기, 음색 전환 금지. "
       "이전 문장과 다음 문장의 음량, 음색, 속도를 일정하게 유지하고 다음 원문을 빠짐없이 그대로 읽으세요. "
       "대본 외 말, 음악, 서두와 마무리 멘트는 넣지 마세요.\n\n"+chunk)
    raw=AUDIO/f"chunk_{index:03d}_raw.wav"
    errors=[]
    for retry in range(6):
        try:
            res=client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")))))
            pkt=next((part.inline_data for part in res.candidates[0].content.parts
                        if getattr(part,"inline_data",None) and part.inline_data.data),None)
            if pkt is None:raise RuntimeError("Empty speech packet")
            blob=pkt.data
            if blob.startswith(b"RIFF"):raw.write_bytes(blob)
            else:
                match=re.search(r"rate=(\d+)",pkt.mime_type or "")
                sr=int(match.group(1)) if match else RATE
                with wave.open(str(raw),"wb") as w:
                    w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(blob)
            run([FF,"-y","-hide_banner","-loglevel","error","-i",str(raw),
               "-af","atempo=1.25,highpass=f=75,lowpass=f=9500,acompressor=threshold=0.12:ratio=1.6:attack=20:release=200, loudnorm=I=-19:TP=-2:LRA=11","-ar",str(RATE),"-ac","1","-c:a","pcm_s16le",str(final)],180)
            if wavduration(final)<3:raise RuntimeError("Empty or truncated speech")
            raw.unlink(missing_ok=True)
            print("TTS_OK",index,round(wavduration(final),1),"sec",flush=True)
            return final
        except Exception as err:
            errors.append(f"{type(err).__name__}:{str(err)[:120]}")
            print("TTS_RETRY",index,retry+1,errors[-1],flush=True)
            if final.exists():final.unlink()
            time.sleep(min(12*(retry+1),65))
    raise RuntimeError(f"Kore generation failed {index}: {errors}")
def source_caption_chunks(text, limit=34):
    # Split source text only at words/punctuation; cap characters for two large subtitle lines.
    toks=list(re.finditer(r"\S+\s*",text))
    spans=[];start=None;end=None
    for tok in toks:
        if start is None:start=tok.start()
        if end is not None and tok.end()-start>limit and end>start:
            spans.append((start,end))
            start=tok.start()
        end=tok.end()
        if text[tok.start():tok.end()].rstrip().endswith((".","?","!")) and end-start>=16:
            spans.append((start,end));start=None;end=None
    if start is not None:spans.append((start,end))
    return [(a,b,text[a:b].strip()) for a,b in spans if text[a:b].strip()]
def exact_sub_timing(text,words,chunkduration):
    # Align the exact source text to independently recognized actual audio words.
    # Absolute subtitle timestamps come from speech recognition, not character-count guesses.
    A=norm(text)
    B=""; asrT=[]
    for w in words:
        nw=norm(w["word"])
        for j in range(len(nw)):
            p=(j+.5)/max(1,len(nw))
            asrT.append(w["start"]+(w["end"]-w["start"])*p)
        B+=nw
    sm=difflib.SequenceMatcher(None,A,B,autojunk=False)
    mapping={}
    matched=0
    for op,i1,i2,j1,j2 in sm.get_opcodes():
        if op=="equal":
            for k in range(i2-i1):
                mapping[i1+k]=asrT[j1+k]
                matched+=1
    coverage=matched/max(1,len(A))
    original_to_normal=[]
    for i,ch in enumerate(text):
        nch=norm(ch)
        if nch:
            original_to_normal.extend([i]*len(nch))
    # A punctuation-free source char timeline mapped to speech.
    ordered=sorted(mapping)
    def time_at(pos):
        if not ordered:return chunkduration*.5
        from bisect import bisect_left
        k=bisect_left(ordered,pos)
        if k<=0:return max(0.01,mapping[ordered[0]]-.08)
        if k>=len(ordered):return min(chunkduration,mapping[ordered[-1]]+.08)
        lo,hi=ordered[k-1],ordered[k]
        return mapping[lo]+(mapping[hi]-mapping[lo])*(pos-lo)/max(1,hi-lo)
    # Map original string index to normalized index
    import bisect
    out=[]
    for start,end,part in source_caption_chunks(text):
        i=bisect.bisect_left(original_to_normal,start)
        j=bisect.bisect_left(original_to_normal,end)-1
        ts=max(0.,time_at(i)-.16)
        te=min(chunkduration,time_at(max(i,j))+.22)
        if te-ts<.28:te=min(chunkduration,ts+.28)
        out.append([ts,te,part])
    # Captions cannot overlap or run backwards.
    for k in range(1,len(out)):
        if out[k][0]<out[k-1][1]:
            m=(out[k][0]+out[k-1][1])/2
            out[k-1][1]=max(out[k-1][0]+.10,m)
            out[k][0]=max(out[k-1][1],m)
        if out[k][1]<=out[k][0]:out[k][1]=out[k][0]+.12
    return out,coverage,B
def ass_t(t):
    cs=int(round(t*100))
    return f"{cs//360000}:{(cs//6000)%60:02}:{(cs//100)%60:02}.{cs%100:02}"
def srt_t(t):
    ms=int(round(t*1000))
    return f"{ms//3600000:02}:{(ms//60000)%60:02}:{(ms//1000)%60:02},{ms%1000:03}"
def two_lines(text,limit=22):
    t=text.strip();chunks=t.split()
    best=None
    for i in range(1,len(chunks)):
        a=" ".join(chunks[:i]);b=" ".join(chunks[i:])
        if len(a)<=limit+4 and len(b)<=limit+4:
            score=max(len(a),len(b))
            if best is None or score<best[0]:best=(score,a,b)
    if best:return best[1]+"\\N"+best[2]
    if len(t)<=limit:return t
    midpoint=len(t)//2
    idx=t.rfind(" ",0,midpoint+5)
    if idx<5:idx=midpoint
    return t[:idx].strip()+"\\N"+t[idx:].strip()
def ass_escape(text):
    return text.replace("{","(").replace("}",")").replace("\\","\\\\")
def loadfont(size,bold=True):
    paths=(["/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
             "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"] if bold else
           ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"])
    for path in paths:
        if Path(path).exists():return ImageFont.truetype(path,size)
    return ImageFont.load_default()
def create_slide(chapter,number,n):
    W,H=1920,1080
    palettes=[
     ((33,32,48),(126,76,79),(245,228,208)),
     ((49,42,45),(117,88,74),(247,228,199)),
     ((34,48,49),(97,115,103),(233,223,192)),
     ((44,39,46),(134,82,97),(243,229,211)),
     ((42,46,42),(105,88,71),(243,222,189)),
     ((29,51,61),(68,105,117),(226,232,233)),
     ((61,44,47),(151,108,84),(249,231,210)),
     ((39,57,55),(83,129,116),(230,235,213)),
    ]
    a,b,cream=palettes[(chapter-1)%8]
    im=Image.new("RGB",(W,H),a)
    d=ImageDraw.Draw(im)
    for y in range(H):
        p=y/H
        col=tuple(round(a[i]*(1-p*.75)+b[i]*p*.75) for i in range(3))
        d.line((0,y,W,y),fill=col)
    # Decorative Korean-drama shapes and soft photographic depth.
    for k in range(13):
        x=(k*283+number*47+chapter*113)%2200-200
        y=(k*149+chapter*77)%850
        rr=30+(k*43)%110
        c=tuple(min(255,v+int((k%3)*5)) for v in b)
        d.ellipse((x-rr,y-rr,x+rr,y+rr),outline=c,width=3)
    face_data=base64.b64decode((ROOT/"somin_reference_face_260.jpg.b64").read_text().strip())
    face=Image.open(io.BytesIO(face_data)).convert("RGB")
    face=ImageOps.fit(face,(760,845),method=Image.Resampling.LANCZOS,centering=(.50,.50))
    face=ImageEnhance.Contrast(face).enhance(1.10)
    mask=Image.new("L",face.size,0);md=ImageDraw.Draw(mask)
    md.rounded_rectangle((20,10,758,844),radius=70,fill=255)
    mask=mask.filter(ImageFilter.GaussianBlur(30))
    im.paste(face,(50,85),mask)
    d=ImageDraw.Draw(im)
    # Translucent high-readability title ribbon on right.
    d.rounded_rectangle((825,120,1850,760),radius=55,fill=(29,27,33))
    d.line((870,220,1800,220),fill=(212,161,108),width=4)
    quotes={
    1:["열네 해 동안","착한 딸로 살았습니다","아버지의 사업이 무너진 날","밤새 그림을 그리던 딸","그 말 한마디가 남았습니다","엄마는 몰랐을까요?"],
    2:["결혼하면 끝날 줄 알았습니다","우리 부모님인데, 미안해","계속되는 생활비 송금","쉬는 법을 잊은 사람","이혼 후 남은 건 두려움","아들의 질문에 멈춰 섰습니다"],
    3:["동생의 전화가 왔습니다","누나만 힘들어?","열네 해 거래 내역","숨겨왔던 진실","동생이 돈을 덜 줄까 봐","그날 처음으로 말했습니다"],
    4:["엄마의 눈물에도 돌아섰습니다","차 안에서 흐른 눈물","엄마, 저도 서러웠어요","저를 버렸다고 하셨습니다","남매가 함께 책임지기로","평생 달라지지 않은 싸움"],
    5:["끝까지 지키려 했던 체면","생활을 줄일 수 없다던 엄마","잘 번다는 말 뒤에","어린 시절의 상처","이제는 원칙을 지켜야 해","그리고 전화 한 통"],
    6:["응급실에서 만난 엄마","이제 어떻게 하니?","이번에는 함께 정해요","처음 펼친 통장","이렇게 많이 쓰는 줄 몰랐다","우리 소민이, 그림 잘 그리지"],
    7:["엄마가 먼저 꺼낸 말","집을 줄여야겠어","잊었던 그림 상자","그림이 그렇게 좋았니?","미술치료 공부 신청","소민이라는 이름으로"],
    8:["반 년이 흘렀습니다","엄마와 마주 앉은 날","정말 몰랐어요?","모르려고 했던 것 같아","다시 시작한 공부","엄마와 나, 서로 다른 길"]
    }
    label=quotes[chapter][number%len(quotes[chapter])]
    font=loadfont(79,True)
    def wrap(s,maxwidth):
        rows=[];cur=""
        for t in s.split(" "):
            trial=(cur+" "+t).strip()
            if d.textbbox((0,0),trial,font=font)[2]>maxwidth and cur:
                rows.append(cur);cur=t
            else:cur=trial
        if cur:rows.append(cur)
        return rows
    rows=wrap(label,880)
    y=300-(len(rows)-1)*40
    for line in rows:
        d.text((880,y),line,font=font,fill=cream,stroke_width=1,stroke_fill=(35,27,31))
        y+=110
    d.text((875,154),f"소민의 인생 이야기  /  {chapter:02}부",font=loadfont(47,True),fill=(224,186,142))
    d.text((890,665),"가족을 사랑하는 것과 내 삶을 지키는 것",font=loadfont(39,False),fill=(222,220,212))
    # Preserve a clean bottom 170px for the subtitle. Only ONE subtitle is shown at a time.
    d.rectangle((0,918,W,H),fill=(20,20,22))
    if chapter==1 and number==0:
        d.text((60,28),"창작 인생사연",font=loadfont(32),fill=(220,200,160))
    path=SLIDES/f"scene_{chapter:02}_{number:02}.jpg"
    im.save(path,quality=88,optimize=True)
    return path
def render_video(ch_durs,full_duration):
    # Gentle paced 30-55 second scene holds, no eye-straining 1-second flashing edits.
    slides=[];global_pos=0.
    for chap,duration in enumerate(ch_durs,1):
        counts=max(5,math.ceil(duration/42.))
        for j in range(counts):
            slide=create_slide(chap,j,counts)
            dt=duration/counts
            slides.append((slide,dt))
            global_pos+=dt
    # concat demuxer variable duration; final still needs repeated last entry.
    path=OUT/"slide_sequence.txt"
    def esc_path(p):return str(p.resolve()).replace("'","'\\''")
    with path.open("w",encoding="utf8") as f:
        for p,secs in slides:
            f.write(f"file '{esc_path(p)}'\n")
            f.write(f"duration {secs:.6f}\n")
        f.write(f"file '{esc_path(slides[-1][0])}'\n")
    target=OUT/"somin_2026_full.mp4"
    cmd=[FF,"-y","-hide_banner","-loglevel","error",
      "-f","concat","-safe","0","-i",str(path),"-i",str(OUT/"somin_narration.wav"),
      "-vf",f"fps=12,ass={str(OUT/'somin_2026.ass')}",
      "-t",f"{full_duration:.3f}","-map","0:v","-map","1:a",
      "-c:v","libx264","-preset","veryfast","-crf","29","-pix_fmt","yuv420p",
      "-c:a","aac","-b:a","128k","-movflags","+faststart",str(target)]
    run(cmd,timeout=9000)
    if target.stat().st_size<1000000:raise RuntimeError("Video file suspiciously small")
    return target,len(slides)

# --- v2 cinematic webtoon adaptation: reference-guided scene storyboard, NOT slide cards ---
SCENE_BEATS={
1:[
"49-year-old Somin learns her mother dismisses two decades of financial help, stunned closeup","Somin confronts her elderly mother in a warm living room, tense eye contact","Early childhood Somin draws on paper with colored pencils, sunlit childhood room","Young Somin says she wants to study art while mother rejects the idea",
"Father's small business collapses, father staring at accounting papers at night","College-age Somin rushes between school and part-time cashier job","Young Somin sketches commissioned illustrations at her cluttered desk","Mother dresses smartly to meet her friends while family finances crumble",
"Young Somin works quietly under a desk lamp late at night","Mother's friends gather noisily around a living-room table playing cards","Exhausted Somin asks her mother for quiet at the doorway","Somin cries into the sketchbook alone after mother scolds her"],
2:[
"Somin marries a kind Korean man in an intimate simple ceremony","Young couple look worried over hospital bills at their kitchen table","Husband helps Somin's frail father carry grocery bags","Somin transfers money to her parents from a phone at night",
"Somin stacks monthly bills and accounting paperwork","Somin teaches a lively group of children to paint at her art classroom","Tired Somin and husband share a quiet unhappy moment","Somin signs divorce papers alone at a desk",
"Single mother Somin calls her elderly mother in a dim living room","Her mother gestures demanding a replacement sofa","Somin reluctantly pays by credit card at furniture shop","Her young son asks a piercing question as Somin hugs him tearfully"],
3:[
"After divorce Somin holds her phone and hesitates to send money","Younger brother calls her angrily, Somin listens in shock","Somin opens a drawer of old bank statements","Closeup Somin calculating decades of transfers at a table",
"Bank statements and receipts scattered around Somin","Somin cries remembering missed holidays with her son","Brother reads photos of remittances on phone and stares amazed","Brother and Somin talk calmly together about aging parents",
"Brother and Somin enter parents' apartment with a paper envelope","Mother looks uneasy as bank records spread across table","Somin stands up and asks whether her own happiness matters","Mother cries while Somin quietly stands her ground"],
4:[
"Somin sits in parked car crying, gripping steering wheel","Somin's young son looks at her kindly across dining table","Somin hugs her son and reassures him","Somin sees three missed calls from mother at night",
"Phone receives mother's remorseful message, Somin replies","Brother talks to Somin sympathetically on phone","Siblings jointly review realistic living expenses","Mother fiercely objects to moving into a less expensive home",
"Somin quietly argues with mother about unaffordable rent","Somin examines an old family photograph","Flashback: once-successful father taking care of everything for mother","Somin by the window realizes she has always shouldered family burdens"],
5:[
"Older mother dresses elegantly and worries about her social standing","Mother sits in large costly apartment and insists she cannot move","Somin opens household spending spreadsheet during phone call","Mother looks annoyed when Somin suggests budgeting",
"Frustrated Somin sits alone staring at her accounts","Flashback: schoolgirl Somin is compared harshly with relatives","Somin sketches in childhood while worrying about mother's judgment","Adult Somin calmly resolves to set limits",
"Somin studies a list of household costs with brother","Elderly mother sits by window looking proud yet fragile","Tense mother and daughter call from separate rooms","Phone rings suddenly with urgent hospital news"],
6:[
"Ambulance arrival outside urban Korean hospital at night","Somin rushes into emergency department corridor","Frail elderly father lies in hospital bed monitored by staff","Mother sits frightened beside father's bed",
"Brother and Somin discuss responsibilities in hospital hallway","Somin calmly tells mother they must decide together","Mother reluctantly opens financial account book","Closeup mother's trembling hands examining expenses",
"Mother and siblings discuss more affordable home","Mother stares in wonder as Somin talks about art","Somin holds elderly mother's hand gently in the hospital","Family watches sunrise through hospital waiting-room window"],
7:[
"Mother says perhaps they should downsize their apartment","Mother packs cherished photo frames carefully into a box","Somin uncovers her forgotten box of art supplies","Somin opens a dusty sketchbook filled with childhood drawings",
"Closeup Somin remembering freedom of painting","Somin visits an art-therapy training classroom","Somin fills in an adult education registration form","Somin presses submit on her phone, emotional but hopeful",
"Mother Somin and brother discuss a new boundary with calm respect","Somin tells her young son she will start studying again","Mother and son laugh together while doing homework","Somin paints a new picture in her sunlit small studio"],
8:[
"Months later Somin reviews affordable family help budget","Somin and mother meet in a small cozy Korean restaurant","Mother serves Somin her favorite side dish","Somin explains how lonely she felt while helping parents",
"Mother admits she avoided knowing how Somin suffered","Mother and Somin quietly wipe away tears across restaurant table","Somin lovingly sets a boundary with her mother","Mother holds Somin's hand as they leave restaurant",
"Mother encourages Somin to continue studying art","Somin walks home under bright afternoon sky","Somin and her young son happily paint together","Somin paints two women walking different paths but still reaching hands"]
}
def _board_path(chapter,board):
    return SLIDES/f"anime_board_{chapter:02d}_{board:02d}.png"
def _make_board(chapter, board):
    dest=_board_path(chapter,board)
    if dest.exists():
        try:
            img=Image.open(dest);img.verify();return dest
        except Exception:dest.unlink()
    beats=SCENE_BEATS[chapter][board*4:(board+1)*4]
    face=base64.b64decode((ROOT/"somin_reference_face_260.jpg.b64").read_text().strip())
    prompt=("MAKE A BEAUTIFUL CINEMATIC KOREAN REALISTIC WEBTOON STORYBOARD, 16:9 LANDSCAPE, EXACTLY "
       "FOUR SEPARATE PANELS in a precise two-column, two-row grid. Four distinct visual shots "
       "with clean thin panel dividers; NONE of the panels should have words, letters, typography, captions, logos, UI, or bubbles. "
       "Depict a dramatic emotional story cinematically using natural Korean interiors, faces, color and lighting. "
       "The attached face photo is the CHARACTER IDENTITY REFERENCE FOR THE MAIN WOMAN SOMIN ONLY: "
       "same slim oval face, large dark almond eyes, long straight black-brown hair, refined features, fair skin, pink lips. "
       "Somin is 49 in adult scenes, looks like the facial reference; younger scenes may age her down. "
       "Never substitute a different woman's face; mother is a separate 70s Korean woman with short gray permed hair. "
       "All four panels should be DIFFERENT CAMERA SHOTS with naturally composed full-screen scenes. "
       "Use elegant realistic Korean drama anime / premium webtoon, soft yet dramatic light, "
       "camera closeups, medium shots and wide establishing shots, detailed backgrounds, rich expressions. "
       "DO NOT generate a poster or thumbnail or title; ONLY clean story footage frames. "
       "Panel top left: "+beats[0]+". Panel top right: "+beats[1]+
       ". Panel bottom left: "+beats[2]+". Panel bottom right: "+beats[3]+".")
    errors=[]
    for attempt in range(4):
        try:
            res=client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[types.Part.from_bytes(data=face,mime_type="image/jpeg"),prompt],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(aspect_ratio="16:9")))
            raw=next((p.inline_data.data for p in res.candidates[0].content.parts
                      if getattr(p,"inline_data",None) and p.inline_data.data),None)
            if not raw:raise RuntimeError("No generated image data")
            im=Image.open(io.BytesIO(raw)).convert("RGB")
            if im.width<640 or im.height<360:raise RuntimeError("Image resolution too low "+str(im.size))
            im.save(dest,optimize=True)
            print("BOARD_OK",chapter,board,im.size,flush=True)
            return dest
        except Exception as exc:
            errors.append(str(exc)[:170]);print("BOARD_RETRY",chapter,board,attempt+1,errors[-1],flush=True)
            time.sleep(min(10*(attempt+1),45))
    raise RuntimeError("Webtoon images not generated. Do not fall back to PPT: "+str(errors))
def _get_panel(chapter,board,panel):
    out=SLIDES/f"anime_panel_{chapter:02d}_{board:02d}_{panel:02d}.jpg"
    if out.exists():return out
    im=Image.open(_make_board(chapter,board)).convert("RGB")
    w,h=im.size
    x=(panel%2)*(w//2);y=(panel//2)*(h//2)
    im=im.crop((x,y,x+w//2,y+h//2))
    # Crop a thin band off panel dividers, then fill 16:9 frame.
    im=im.crop((round(im.width*.018),round(im.height*.026),
                round(im.width*.982),round(im.height*.974)))
    im=ImageOps.fit(im,(1920,1080),method=Image.Resampling.LANCZOS)
    im.save(out,quality=88,optimize=True)
    return out
def _make_shot(path,chapter,board,panel,phase):
    dest=SLIDES/f"shot_{chapter:02d}_{board:02d}_{panel:02d}_{phase}.jpg"
    if dest.exists():return dest
    im=Image.open(path).convert("RGB")
    # Three distinct compositions per anime scene (wide, emotional close-up, shifted POV).
    if phase in (1,2):
        z=1.13 if phase==1 else 1.19
        cw=int(1920/z);ch=int(1080/z)
        center=.44 if phase==1 else .57
        x=max(0,min(1920-cw,round(1920*center-cw/2)))
        y=max(0,min(1080-ch,round(1080*.48-ch/2)))
        im=im.crop((x,y,x+cw,y+ch)).resize((1920,1080),Image.Resampling.LANCZOS)
    # Gentle bottom gradation only, no distracting slide-style labels or rectangles.
    cover=Image.new("RGBA",im.size,(0,0,0,0));v=ImageDraw.Draw(cover)
    for yy in range(830,1080,3):
        alpha=int(165*(yy-830)/250)
        v.rectangle((0,yy,1920,min(1080,yy+3)),fill=(0,0,0,alpha))
    im=Image.alpha_composite(im.convert("RGBA"),cover).convert("RGB")
    im.save(dest,quality=87,optimize=True)
    return dest
def render_video(ch_durs,full_duration):
    shots=[];duration_sum=0.
    for chapter,duration in enumerate(ch_durs,1):
        for board in range(3):
            _make_board(chapter,board)
        clips=12*3
        for j in range(12):
            board,panel=divmod(j,4)
            path=_get_panel(chapter,board,panel)
            for phase in range(3):
                dest=_make_shot(path,chapter,board,panel,phase)
                dt=duration/clips
                shots.append((dest,dt))
                duration_sum+=dt
    sequence=OUT/"cinematic_shots.txt"
    with sequence.open("w",encoding="utf8") as f:
        for p,dt in shots:
            pp=str(p.resolve()).replace("'","'\\''")
            f.write("file '"+pp+"'\n")
            f.write("duration %.6f\n"%dt)
        f.write("file '"+str(shots[-1][0].resolve())+"'\n")
    target=OUT/"somin_2026_cinematic_v2.mp4"
    # Gentle animated zoom, 6-8 second scene changes, no slideshow title cards.
    vf="fps=15,zoompan=z='min(zoom+0.00050,1.11)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=15,ass="+str(OUT/"somin_2026.ass")
    cmd=[FF,"-y","-hide_banner","-loglevel","error",
       "-f","concat","-safe","0","-i",str(sequence),"-i",str(OUT/"somin_narration.wav"),
       "-vf",vf,"-t",f"{full_duration:.3f}","-map","0:v","-map","1:a",
       "-c:v","libx264","-preset","ultrafast","-crf","24","-pix_fmt","yuv420p",
       "-c:a","aac","-b:a","128k","-movflags","+faststart",str(target)]
    print("CINEMATIC_RENDER_START","shots",len(shots),"duration",round(full_duration),flush=True)
    run(cmd,timeout=9000)
    if target.stat().st_size<5_000_000:raise RuntimeError("Cinematic output too small")
    return target,len(shots)

def main():
    idx=0;records=[];chunkmap=[]
    for ch in STORY["chapters"]:
        for part in split_chunks(ch["text"]):
            idx+=1
            chunkmap.append(dict(chapter=ch["title"],chapter_no=STORY["chapters"].index(ch)+1,
                                 index=idx,original=part))
    print("TOTAL_TTS_CHUNKS",len(chunkmap),flush=True)
    audio_files=[]
    for item in chunkmap:
        wav=synth(item["original"],item["index"])
        item["wav"]=str(wav);item["duration"]=wavduration(wav)
        audio_files.append(wav)
        time.sleep(6)
    # Transcript timing starts from the rendered, speed-adjusted WAV.
    from faster_whisper import WhisperModel
    model=WhisperModel("base",device="cpu",compute_type="int8",cpu_threads=4,num_workers=1)
    allcapt=[];offset=.35;QA=[]
    chapter_secs={i:0. for i in range(1,9)}
    silence=.18
    for item in chunkmap:
        segments,info=model.transcribe(item["wav"],language="ko",beam_size=3,
            word_timestamps=True,vad_filter=False,condition_on_previous_text=False)
        words=[]
        for s in segments:
            for w in (s.words or []):
                if w.end>w.start:words.append(dict(start=float(w.start),end=float(w.end),word=w.word))
        if not words:raise RuntimeError(f"No ASR words for TTS chunk {item['index']}")
        grouped,coverage,asrtxt=exact_sub_timing(item["original"],words,item["duration"])
        if coverage<.58:raise RuntimeError(
            f"Chunk {item['index']} has low text/audio agreement {coverage:.2f}; check TTS before exporting")
        for start,end,txt in grouped:
            allcapt.append(dict(start=round(offset+start,3),end=round(offset+end,3),
                  text=txt,chapter=item["chapter_no"],chunk=item["index"]))
        QA.append(dict(index=item["index"],coverage=round(coverage,3),
                       duration=round(item["duration"],2),asr_char_count=len(asrtxt)))
        offset+=item["duration"]+silence
        chapter_secs[item["chapter_no"]]+=item["duration"]+silence
        if item["index"]%8==0:print("ASR_ALIGNED",item["index"],len(chunkmap),flush=True)
    # Prepare exact-length PCM. A leader plus 180ms silence after each chunk.
    fullwav=OUT/"somin_narration.wav"
    with wave.open(str(fullwav),"wb") as output:
        output.setnchannels(1);output.setsampwidth(2);output.setframerate(RATE)
        output.writeframes(b"\0"*(int(.35*RATE)*2))
        for item in chunkmap:
            with wave.open(item["wav"],"rb") as incoming:
                assert incoming.getframerate()==RATE
                output.writeframes(incoming.readframes(incoming.getnframes()))
            output.writeframes(b"\0"*(int(silence*RATE)*2))
    duration=wavduration(fullwav)
    (OUT/"somin_2026_speech_alignment_QA.json").write_text(
        json.dumps({"duration_seconds":duration,"voice":"Kore","speed":1.25,
         "caption_count":len(allcapt),"chapters":chapter_secs,"qa":QA},ensure_ascii=False,indent=2),encoding="utf8")
    (OUT/"somin_2026_captions.json").write_text(json.dumps(allcapt,ensure_ascii=False,indent=2),encoding="utf8")
    srt=[];events=[]
    for n,c in enumerate(allcapt,1):
        srt.append(f"{n}\n{srt_t(c['start'])} --> {srt_t(c['end'])}\n{c['text']}\n")
        line=two_lines(ass_escape(c["text"]))
        events.append(f"Dialogue: 0,{ass_t(c['start'])},{ass_t(c['end'])},Senior,,0,0,0,,{line}")
    (OUT/"somin_2026.srt").write_text("\n".join(srt),encoding="utf8")
    style="""[Script Info]
Title: 소민 인생사연 - Kore 1.25
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes
WrapStyle: 2
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Senior,Noto Sans CJK KR,72,&H00FFFFFF,&H00FFFFFF,&H00000000,&H98000000,-1,0,0,0,100,100,0,0,3,3,0,2,105,105,68,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    (OUT/"somin_2026.ass").write_text(style+"\n".join(events)+"\n",encoding="utf8")
    run([FF,"-y","-hide_banner","-loglevel","error","-i",str(fullwav),
         "-c:a","libmp3lame","-b:a","128k",str(OUT/"somin_2026_kore125.mp3")],timeout=2700)
    # Chapter durations include exactly the 180ms between chunks so scene timing stays aligned.
    target,scene_count=render_video([chapter_secs[i] for i in range(1,9)],duration)
    print("FINISHED",json.dumps({"video":target.name,"bytes":target.stat().st_size,
     "duration_sec":round(duration,1),"clips":len(chunkmap),"scenes":scene_count,
     "captions":len(allcapt),"min_coverage":min(z["coverage"] for z in QA)},
     ensure_ascii=False),flush=True)
if __name__=="__main__":
    try:main()
    except Exception:
        traceback.print_exc()
        raise
