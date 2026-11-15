#!/usr/bin/env python3
# Somin 8-chapter long-form production: one female Kore narration, speech-derived subtitles, 1080p MP4.
# Output in somin_v3_output. Fictionalized characters; no user personal data or real names.
import os, re, io, json, time, math, wave, base64, difflib, shutil, subprocess, traceback, unicodedata
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
from google import genai
from google.genai import types

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"somin_v3_audio_output"
AUDIO=OUT/"audio_chunks"; SLIDES=OUT/"slides"
for p in (OUT,AUDIO,SLIDES):p.mkdir(parents=True,exist_ok=True)
STORY=json.loads((ROOT/"somin_longform_story_2026.json").read_text(encoding="utf8"))
SPEED=1.0
RATE=24000
CAP=310
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
    final=AUDIO/f"chunk_{index:03d}_natural.wav"
    if final.exists() and wavduration(final)>2:return final
    prompt=("당신은 마흔아홉 살 한국 여성 소민입니다. 오직 한 명의 차분한 성인 여성의 자연스러운 한국어 목소리로 다음 글을 빠짐없이 읽으세요. 인용된 다른 인물의 대사에서도 음색이나 화자 정체성을 바꾸지 말고, 약간의 억양 차이만 사용하세요. 과장된 연기, 성대모사, 속삭임, 효과음, 덧붙이는 설명은 하지 마세요. 본문:\n" + chunk)
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
               "-ar",str(RATE),"-ac","1","-c:a","pcm_s16le",str(final)],180)
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
    target=OUT/"somin_v3_full.mp4"
    cmd=[FF,"-y","-hide_banner","-loglevel","error",
      "-f","concat","-safe","0","-i",str(path),"-i",str(OUT/"somin_narration.wav"),
      "-vf",f"fps=12,ass={str(OUT/'somin_v2.ass')}",
      "-t",f"{full_duration:.3f}","-map","0:v","-map","1:a",
      "-c:v","libx264","-preset","veryfast","-crf","29","-pix_fmt","yuv420p",
      "-c:a","aac","-b:a","128k","-movflags","+faststart",str(target)]
    run(cmd,timeout=9000)
    if target.stat().st_size<1000000:raise RuntimeError("Video file suspiciously small")
    return target,len(slides)
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
    (OUT/"somin_v3_speech_alignment_QA.json").write_text(
        json.dumps({"duration_seconds":duration,"voice":"Kore","speed":1.0,
         "caption_count":len(allcapt),"chapters":chapter_secs,"qa":QA},ensure_ascii=False,indent=2),encoding="utf8")
    (OUT/"somin_v3_captions.json").write_text(json.dumps(allcapt,ensure_ascii=False,indent=2),encoding="utf8")
    srt=[];events=[]
    for n,c in enumerate(allcapt,1):
        srt.append(f"{n}\n{srt_t(c['start'])} --> {srt_t(c['end'])}\n{c['text']}\n")
        line=two_lines(ass_escape(c["text"]))
        events.append(f"Dialogue: 0,{ass_t(c['start'])},{ass_t(c['end'])},Senior,,0,0,0,,{line}")
    (OUT/"somin_v2.srt").write_text("\n".join(srt),encoding="utf8")
    style="""[Script Info]
Title: 소민 인생사연 - Kore 자연속도 1.0
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
    (OUT/"somin_v2.ass").write_text(style+"\n".join(events)+"\n",encoding="utf8")
    run([FF,"-y","-hide_banner","-loglevel","error","-i",str(fullwav),
         "-c:a","libmp3lame","-b:a","128k",str(OUT/"somin_v3_kore_normal.mp3")],timeout=2700)
    # Chapter durations include exactly the 180ms between chunks so scene timing stays aligned.
    print("AUDIO_V2_FINISHED",json.dumps({"duration_sec":round(duration,1),"clips":len(chunkmap),"captions":len(allcapt),"min_coverage":min(z["coverage"] for z in QA)},ensure_ascii=False),flush=True)
if __name__=="__main__":
    try:main()
    except Exception:
        traceback.print_exc()
        raise
