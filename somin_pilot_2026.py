#!/usr/bin/env python3
# Cost-capped Somin 1-2 minute proof: single Kore voice, clean reference-guided anime panels, timed captions.
import os,io,re,json,time,wave,base64,shutil,subprocess
from pathlib import Path
from PIL import Image, ImageOps
from google import genai
from google.genai import types

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"somin_pilot_output"
OUT.mkdir(exist_ok=True)
ff=shutil.which("ffmpeg") or "ffmpeg"
key=os.getenv("GEMINI_API_KEY")
if not key:
    raise RuntimeError("GEMINI_API_KEY missing; never swap voice or provider.")
client=genai.Client(api_key=key)
def cmd(*a,timeout=2400):
    subprocess.run(list(a),check=True,timeout=timeout)
def duration(p):
    with wave.open(str(p),"rb") as f:return f.getnframes()/f.getframerate()
def charsplit(t,count=2):
    sentences=[x.strip() for x in re.split(r"(?<=[.!?])\s+",re.sub(r"\s+"," ",t)) if x.strip()]
    mid=len(t)/count
    parts=[];acc=""
    for s in sentences:
        if acc and len(acc)+len(s)+1>mid and len(parts)<count-1:
            parts.append(acc);acc=""
        acc=(acc+" "+s).strip()
    if acc:parts.append(acc)
    return parts

story=json.loads((ROOT/"somin_longform_story_2026.json").read_text(encoding="utf8"))
t=re.sub(r"\s+"," ",story["chapters"][0]["text"]).strip()
cut=t.rfind(".",0,940)
if cut<650:raise RuntimeError("Could not identify a safe story boundary")
text=t[:cut+1]
parts=charsplit(text,2)
assert len(parts)==2 and len(text)>650
(OUT/"pilot_script.txt").write_text(text,encoding="utf8")
(OUT/"pilot_manifest.json").write_text(json.dumps({
    "fiction":True,"somin_support_duration":"20년 넘게",
    "voice":"Kore","speed":1.25,"duration_target":"1–2min",
    "source":"somin_longform_story_2026.json 1부, opening passage",
    "chunks":len(parts),"type":"proof of concept; NOT full film"
},ensure_ascii=False,indent=2),encoding="utf8")
print("SCRIPT",len(text),len(parts),flush=True)

wavefiles=[]
voice_prompt=(
 "오직 한 사람의 49세 한국 여성 소민이 들려주는 일인칭 오디오북입니다. "
 "여성 성우 Kore 한 명의 담백한 목소리로 처음부터 끝까지 음색과 음높이, "
 "강세, 템포, 녹음 볼륨을 일정하게 유지하여 자연스럽게 읽어주세요. "
 "엄마, 아빠, 아이의 인용 대사까지 절대로 성우나 목소리를 바꾸거나 "
 "다른 등장인물로 연기하지 마세요. 울거나 비명을 지르거나 과장하지 마세요. "
 "대본에 적힌 글자만 빠짐없이 그대로 낭독하고 추가 대사는 넣지 마세요. "
 "이하 원문만 읽으세요:\n\n")
for n,part in enumerate(parts,1):
    dest=OUT/f"pilot_voice_{n:02d}.wav"
    if not dest.exists():
        last=None
        for trial in range(3):
            try:
                response=client.models.generate_content(
                    model="gemini-2.5-flash-preview-tts",
                    contents=voice_prompt+part,
                    config=types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                          voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")))))
                pkt=next((x.inline_data for x in response.candidates[0].content.parts
                          if getattr(x,"inline_data",None) and x.inline_data.data),None)
                if not pkt:raise ValueError("Gemini returned empty speech")
                raw=OUT/f"raw_{n:02d}.wav"
                if pkt.data.startswith(b"RIFF"):raw.write_bytes(pkt.data)
                else:
                    rate=re.search(r"rate=(\d+)",pkt.mime_type or "")
                    with wave.open(str(raw),"wb") as o:
                        o.setnchannels(1);o.setsampwidth(2)
                        o.setframerate(int(rate.group(1)) if rate else 24000)
                        o.writeframes(pkt.data)
                cmd(ff,"-y","-v","error","-i",str(raw),"-af",
                    "atempo=1.25,highpass=f=75,lowpass=f=9000,acompressor=threshold=0.11:ratio=1.5:attack=15:release=230",
                    "-ar","24000","-ac","1",str(dest),timeout=120)
                if duration(dest)<8:raise ValueError("TTS output implausibly short")
                raw.unlink(missing_ok=True)
                break
            except Exception as e:
                last=e;msg=str(e)
                print("TTS_ERROR",n,trial+1,msg[:800],flush=True)
                dest.unlink(missing_ok=True)
                if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                    # Hard budget guard: no huge retry loops when quota/billing project is exhausted.
                    raise RuntimeError("GEMINI_QUOTA_429: stop pilot, inspect paid project/key and quota. No more paid calls.") from e
                if trial==2:raise
                time.sleep(12*(trial+1))
    wavefiles.append(dest)
    print("VOICE_OK",n,round(duration(dest),2),"Kore",flush=True)
    time.sleep(15)

pause=0.25
audio=OUT/"pilot_narration.wav"
with wave.open(str(audio),"wb") as o:
    o.setnchannels(1);o.setsampwidth(2);o.setframerate(24000)
    for p in wavefiles:
        with wave.open(str(p),"rb") as i:
            o.writeframes(i.readframes(i.getnframes()))
        o.writeframes(bytes(int(24000*pause)*2))
total=duration(audio)
print("AUDIO_DURATION",total,flush=True)

# Voice-derived text captions, no estimated per-character timestamps.
from faster_whisper import WhisperModel
model=WhisperModel("base",device="cpu",compute_type="int8")
segs,info=model.transcribe(str(audio),language="ko",word_timestamps=True,
                           condition_on_previous_text=False)
captions=[]
pending=[];st=None;en=None
for seg in segs:
    for wd in (seg.words or []):
        w=wd.word.strip()
        if not w:continue
        if st is None:st=float(wd.start)
        pending.append(w);en=float(wd.end)
        if len(" ".join(pending))>=25 or w.endswith((".","?","!")):
            captions.append([st,en," ".join(pending)])
            pending=[];st=None;en=None
if pending and st is not None:captions.append([st,en," ".join(pending)])
if len(captions)<10:raise RuntimeError("Subtitle recognition unexpectedly short")
def ass_time(s):
    cs=round(s*100)
    return f"{cs//360000}:{(cs//6000)%60:02}:{(cs//100)%60:02}.{cs%100:02}"
def srt_time(s):
    ms=round(s*1000)
    return f"{ms//3600000:02}:{(ms//60000)%60:02}:{(ms//1000)%60:02},{ms%1000:03}"
def wrap(t):
    a=t.split();cut=round(len(a)/2)
    if len(t)>23 and cut>0:return " ".join(a[:cut])+r"\N"+" ".join(a[cut:])
    return t
ass_header="""[Script Info]
Title: Somin pilot Kore
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Somin,Noto Sans CJK KR,72,&H00FFFFFF,&H00FFFFFF,&H00000000,&H85000000,-1,0,0,0,100,100,0,0,3,3,0,2,105,105,66,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
events=[];srt=[]
for i,(st,en,t) in enumerate(captions,1):
    t=t.replace("{","(").replace("}",")")
    events.append(f"Dialogue: 0,{ass_time(st)},{ass_time(en)},Somin,,0,0,0,,{wrap(t)}")
    srt.append(f"{i}\n{srt_time(st)} --> {srt_time(en)}\n{t}\n")
(OUT/"pilot.ass").write_text(ass_header+"\n".join(events)+"\n",encoding="utf8")
(OUT/"pilot.srt").write_text("\n".join(srt),encoding="utf8")
print("CAPTIONS",len(captions),flush=True)

# 3 image generations maximum: each produces 2x2 distinct cinematic story panels.
ref=base64.b64decode((ROOT/"somin_reference_face_260.jpg.b64").read_text().strip())
beats=[
[
"Adult Korean woman Somin sits stunned in her small apartment after her mother disowns two decades of financial help, cinematic tearful face closeup",
"Elderly Korean mother confronts adult Somin in a modest home living room, tense emotional two-shot",
"Somin silently studies twenty years of worn bank passbooks and receipts at her desk",
"Adult Somin holds her phone under warm lamplight, face reflecting disbelief and hurt"
],[
"Somin as a young girl sketches joyful colors in a sunlit childhood bedroom",
"Younger Somin stands next to fashionably dressed mother during the family's wealthy years, outdoor neighborhood",
"Teenage Somin proudly shows her artwork to her mother at the dining table",
"Mother dismisses her art-school dream; girl looks down at the drawing in disappointment"
],[
"Korean father reviews business ledgers in a dark office after his business fails, worried wide shot",
"University-age Somin works as a part-time cashier in a busy shop",
"Young Somin draws a commissioned illustration past midnight at a dim desk lamp",
"Somin stands emotionally drained in the doorway while older mother hosts laughing guests in the living room"
]]
panels=[]
for b,scenes in enumerate(beats):
    board=OUT/f"board_{b:02d}.png"
    if not board.exists():
        prompt=(
         "Premium Korean melodrama illustration with cinematic realistic-webtoon aesthetic, "
         "soft photorealistic anime textures and natural expressive faces. "
         "Produce one single wide 16:9 image exactly divided into FOUR RECTANGULAR PANELS "
         "on a 2x2 grid with thin panel lines. Each panel must depict a distinct scene, "
         "not a poster or presentation. IMPORTANT reference picture is the exact identity "
         "of female protagonist SOMIN: slim oval face, long straight dark brown hair, "
         "large almond eyes, fair skin, refined natural features. Keep Somin consistent. "
         "Mother is an entirely separate elderly Korean woman with gray curly hair. "
         "Shots vary: wide, medium, close-up, cutaway. Cinematic natural lighting "
         "and detailed homes, 16:9 framing within every panel. "
         "ABSOLUTELY NO TEXT, CAPTIONS, KOREAN LETTERS, SPEECH BUBBLES, TITLES, WATERMARKS, NUMBERS. "
         "Panel upper left: "+scenes[0]+". Upper right: "+scenes[1]+
         ". Lower left: "+scenes[2]+". Lower right: "+scenes[3]+"."
        )
        try:
            response=client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[types.Part.from_bytes(data=ref,mime_type="image/jpeg"),prompt],
                config=types.GenerateContentConfig(response_modalities=["IMAGE"],
                  image_config=types.ImageConfig(aspect_ratio="16:9")))
            blob=next((x.inline_data.data for x in response.candidates[0].content.parts
                       if getattr(x,"inline_data",None) and x.inline_data.data),None)
            if not blob:raise RuntimeError("Empty Gemini image; no PPT fallback")
            im=Image.open(io.BytesIO(blob)).convert("RGB")
            if im.width<640:raise RuntimeError("Image too small")
            im.save(board,optimize=True)
        except Exception as e:
            raise RuntimeError("Anime image generation failed, no PPT fallback: "+str(e)[:900]) from e
    im=Image.open(board).convert("RGB")
    w,h=im.size
    for k in range(4):
        x=(k%2)*(w//2);y=(k//2)*(h//2)
        tile=im.crop((x,y,x+w//2,y+h//2))
        tile=ImageOps.fit(tile,(1920,1080),method=Image.Resampling.LANCZOS)
        fp=OUT/f"shot_{b:02d}_{k:02d}.jpg";tile.save(fp,quality=88)
        panels.append(fp)
    print("BOARD_OK",b,im.size,flush=True)
    time.sleep(12)

# 12 narrative scenes, 2 reframes each, approximately 3-6 seconds per cut.
shots=[]
for p in panels:
    im=Image.open(p).convert("RGB")
    shots.append(p)
    w,h=im.size;z=1.14;cw=int(w/z);ch=int(h/z)
    x=int(w*.53-cw/2);y=int(h*.47-ch/2)
    x=max(0,min(w-cw,x));y=max(0,min(h-ch,y))
    crop=im.crop((x,y,x+cw,y+ch)).resize((w,h),Image.Resampling.LANCZOS)
    alt=OUT/(p.stem+"_detail.jpg");crop.save(alt,quality=87)
    shots.append(alt)
seq=OUT/"pilot_shots.txt"
with seq.open("w") as f:
    for p in shots:
        f.write("file '"+str(p.resolve())+"'\n")
        f.write(f"duration {total/len(shots):.8f}\n")
    f.write("file '"+str(shots[-1].resolve())+"'\n")
target=OUT/"somin_1to2min_proof.mp4"
vf="fps=12,zoompan=z='min(zoom+0.00055,1.09)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=12,ass="+str(OUT/"pilot.ass")
cmd(ff,"-y","-v","error","-f","concat","-safe","0","-i",str(seq),
    "-i",str(audio),"-vf",vf,"-t",f"{total:.3f}",
    "-map","0:v","-map","1:a","-c:v","libx264","-preset","veryfast",
    "-crf","26","-pix_fmt","yuv420p","-c:a","aac","-b:a","128k",
    "-movflags","+faststart",str(target),timeout=9000)
print("PILOT_FINISHED",json.dumps({"duration":round(total,1),"bytes":target.stat().st_size,
      "base_scenes":12,"edit_cuts":len(shots),"captions":len(captions),
      "voice":"Kore","speed":1.25,"somin_support":"20 years+"}),flush=True)
