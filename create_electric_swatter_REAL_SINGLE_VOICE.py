"""Rebuild the electric swatter short with REAL licensed photographs and a SINGLE TTS take.

No illustrated fly swatter and no separately synthesized voice lines.
Actual continuous audio is independently transcribed and checked for an exact single
closing CTA BEFORE any finished MP4 is published.
"""
import difflib, io, json, math, os, re, subprocess, time, wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance
import imageio_ffmpeg, requests
from google import genai
from google.genai import types

OUT=Path("electric_swatter_real_retake")
OUT.mkdir(parents=True,exist_ok=True)
FF=imageio_ffmpeg.get_ffmpeg_exe()
W,H=720,1280
RATE=1.25
LINES=[
("전기 모기채에 손이 닿으면 어떻게 될까요?","손이 닿으면 어떻게 될까?","swatter"),
("금속망에 전기가 흐를 때 만지면 순간적으로 찌릿한 감전을 느낄 수 있습니다.","금속망에 닿으면 감전 위험","swatter"),
("깜짝 놀라 손을 급히 빼다가 다치거나 피부에 화상을 입을 수도 있어요.","놀람 · 통증 · 화상 위험","mosquito"),
("그런데 더 중요한 건, 전원을 껐다고 바로 안전해지는 건 아니라는 사실입니다.","전원을 꺼도 즉시 안전한 건 아님","swatter"),
("일부 전기 모기채는 전원을 끈 뒤에도 금속망에 전기가 잠시 남을 수 있습니다.","전원 OFF 후에도 잔류 전기 주의","swatter"),
("제품 사용설명서에 따라 사용하고, 어린이가 만지지 못하도록 보관하세요.","아이 손 닿지 않게 보관","mosquito"),
("가연성 살충제가 뿌려진 곳에서는 사용하지 말고, 호기심에 손으로 시험하지도 마세요.","가연성 살충제 근처 사용 금지","swatter"),
("안전한 생활 습관, 꼭 기억해 두세요.","안전한 사용 습관 꼭 기억하세요","mosquito"),
("도움이 됐다면 구독과 좋아요! 생활알고리즘.","구독과 좋아요", "outro"),
]
assert sum(line.count("구독과 좋아요") for line,_,_ in LINES)==1
assert all("구독" not in line+cap and "좋아요" not in line+cap for line,cap,_ in LINES[:-1])
SCRIPT="\n".join(line for line,_,_ in LINES)
ASSETS=[
 # Actual product photographs under free public-use licenses; no AI imagery.
 ("swatter", "https://cdn.pixabay.com/photo/2017/07/07/05/52/electric-fly-swatter-2480471_1280.jpg", "Pixabay Content License", "https://pixabay.com/photos/electric-fly-swatter-2480471/"),
 ("swatter","https://images.weserv.nl/?url=upload.wikimedia.org/wikipedia/commons/1/19/Raketnyamuk.jpg&w=1100","Public domain (Hayabusa future)","https://commons.wikimedia.org/wiki/File:Raketnyamuk.jpg"),
 ("swatter","https://images.weserv.nl/?url=upload.wikimedia.org/wikipedia/commons/1/1d/Elektronische_Fliegenklatsche.jpg&w=800","Public domain (Journey234)","https://commons.wikimedia.org/wiki/File:Elektronische_Fliegenklatsche.jpg"),
 ("swatter","https://upload.wikimedia.org/wikipedia/commons/1/19/Raketnyamuk.jpg","Public domain (Hayabusa future)","https://commons.wikimedia.org/wiki/File:Raketnyamuk.jpg"),
 ("mosquito","https://images.pexels.com/photos/12972049/pexels-photo-12972049.jpeg?auto=compress&cs=tinysrgb&w=1300","Pexels License", "https://www.pexels.com/photo/close-up-shot-of-a-mosquito-on-human-skin-12972049/"),
 ("mosquito","https://images.pexels.com/photos/6439698/pexels-photo-6439698.jpeg?auto=compress&cs=tinysrgb&w=1300","Pexels License", "https://www.pexels.com/photo/close-up-photo-of-a-mosquito-6439698/"),
 ("mosquito","https://images.pexels.com/photos/762935/pexels-photo-762935.jpeg?auto=compress&cs=tinysrgb&w=1300","Pexels License", "https://www.pexels.com/photo/black-mosquito-closeup-photo-762935/"),
]
VIDEO_ID=30646701
VIDEO_SOURCE="https://www.pexels.com/video/close-up-of-insect-on-grass-blade-30646701/"
SOURCES=[
 "https://www.kca.go.kr/home/sub.do?menukey=4006&mode=view&no=1002833023&page=3",
 "https://www.pexels.com/license/",
 "https://pixabay.com/service/license-summary/"
]
S=requests.Session()
S.headers.update({"User-Agent":"Mozilla/5.0 (compatible; educational Shorts production)"})

def run(*args,timeout=120):
 subprocess.run([FF,"-y","-hide_banner","-loglevel","error",*map(str,args)],
                check=True,timeout=timeout,stdout=subprocess.DEVNULL)

def probe_duration(path):
 p=subprocess.run([FF,"-hide_banner","-i",str(path)],capture_output=True,text=True,timeout=20)
 m=re.search(r"Duration:\s*(\d\d):(\d\d):(\d\d\.\d+)",p.stderr)
 if not m:raise ValueError("cannot probe duration of "+str(path))
 return int(m.group(1))*3600+int(m.group(2))*60+float(m.group(3))

def fontpath():
 for p in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
           "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
           "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"]:
  if Path(p).exists():return p
 p=OUT/"NanumGothic-Bold.ttf"
 if not p.exists():
  r=S.get("https://raw.githubusercontent.com/google/fonts/main/ofl/nanumgothic/NanumGothic-Bold.ttf",timeout=25)
  r.raise_for_status();p.write_bytes(r.content)
 return str(p)
FONT=fontpath()
def font(sz):return ImageFont.truetype(FONT,sz)

def download_photos():
 photos={"swatter":[],"mosquito":[]}
 credits=[]
 for category,url,license,page in ASSETS:
  path=OUT/f"photo_{category}_{len(photos[category])}.jpg"
  try:
   r=S.get(url,timeout=(8,35))
   r.raise_for_status()
   if "image" not in r.headers.get("content-type","").lower():raise ValueError("Not an image")
   img=Image.open(io.BytesIO(r.content)).convert("RGB")
   if min(img.size)<350:raise ValueError("small photograph")
   img.save(path,quality=92)
   photos[category].append(path)
   credits.append(f"{page} | {license} | modified with slow image motion")
   print("REAL_PHOTO",category,url[:95],"YES",img.size,flush=True)
  except Exception as exc:
   print("REAL_PHOTO",category,url[:95],"NO",str(exc)[:110],flush=True)
 if not photos["swatter"]:raise RuntimeError("No REAL photographed electric swatter available; do not publish illustrations.")
 if not photos["mosquito"]:raise RuntimeError("No REAL mosquito macro photo available.")
 (OUT/"photo_credits.txt").write_text("\n".join(credits),encoding="utf-8")
 return photos

def download_insect_video():
 # Optional B-roll that is REAL motion; don't misrepresent this as an electric swatter clip.
 path=OUT/"real_insect_broll.mp4"
 for fps in (30,25,24):
  for dim in ("1920_1080","1080_1920","1280_720","720_1280","960_540"):
   u=f"https://videos.pexels.com/video-files/{VIDEO_ID}/{VIDEO_ID}-hd_{dim}_{fps}fps.mp4"
   try:
    resp=S.head(u,timeout=4)
    if resp.status_code!=200 or "video" not in resp.headers.get("content-type","").lower():continue
    with S.get(u,stream=True,timeout=(8,65)) as r:
     r.raise_for_status()
     with path.open("wb") as f:
      total=0
      for chunk in r.iter_content(256*1024):
       if chunk:
        total+=len(chunk)
        if total>50_000_000:raise ValueError("Video >50MB")
        f.write(chunk)
    if path.stat().st_size>100000:
     print("REAL_BROLL_OK",u,flush=True)
     return path
   except Exception:pass
   path.unlink(missing_ok=True)
 print("REAL_BROLL_UNAVAILABLE; will animate actual photographs",flush=True)
 return None

def audio_generate():
 c=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
 prompt=(
 "Korean short informational narration. A SINGLE continuous male narrator, one stable speaking voice, "
 "natural Korean pronunciation, calm confident documentary-style delivery. "
 "Speak the text below exactly once from beginning to end. "
 "No headings, added words, interjections, repeats, ads or slogans beyond the provided text. "
 "Do not read the delimiters. Entire narration should be one continuous take.\n\n"
 "=== BEGIN NARRATION ===\n"+SCRIPT+"\n=== END NARRATION ==="
 )
 for attempt in range(3):
  try:
   r=c.models.generate_content(
    model="gemini-2.5-flash-preview-tts",
    contents=prompt,
    config=types.GenerateContentConfig(response_modalities=["AUDIO"],
      speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
       prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
   items=r.candidates[0].content.parts
   blob=next((p.inline_data for p in items if p.inline_data and p.inline_data.data),None)
   if not blob:raise RuntimeError("Gemini returned no TTS audio")
   raw=OUT/"full_single_take.wav"
   if blob.data.startswith(b"RIFF"):raw.write_bytes(blob.data)
   else:
    m=re.search(r"rate=(\d+)",blob.mime_type or "")
    sr=int(m.group(1)) if m else 24000
    with wave.open(str(raw),"wb") as f:
     f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr);f.writeframes(blob.data)
   with wave.open(str(raw),"rb") as f:
    secs=f.getnframes()/f.getframerate()
   if not 18<=secs<=92:raise RuntimeError("Unreasonable single take duration: "+str(secs))
   print("ONE_TAKE_GENERATED",round(secs,2),"seconds",flush=True)
   resp=c.models.generate_content(
    model="gemini-3.8-flash",
    contents=["이 오디오에서 실제 발화된 한국어를 생략 없이 모두 그대로 받아쓰세요. 설명이나 다른 문구를 추가하지 마세요.",
      types.Part.from_bytes(data=raw.read_bytes(),mime_type="audio/wav")])
   spoken=(resp.text or "").strip()
   normalized=re.sub(r"[^가-힣A-Za-z0-9]","",spoken)
   match=normalized.count("구독")==1 and normalized.count("좋아요")==1
   similarity=difflib.SequenceMatcher(None,re.sub(r"[^가-힣A-Za-z0-9]","",SCRIPT),normalized).ratio()
   print("TRANSCRIPT",spoken,flush=True)
   print("ASR_VERIFIED_SINGLE_TAKE",match,"SIMILARITY",round(similarity,2),flush=True)
   if not match or similarity<0.74:raise RuntimeError("TTS added unexpected words or CTA")
   wav=OUT/"narration_125.wav"
   run("-i",raw,"-af","atempo=1.25","-ar","24000","-ac","1",wav)
   (OUT/"actual_audio_qa.json").write_text(json.dumps({
     "single_continuous_take":True,"voice":"Gemini Charon","speed":1.25,
     "spoken_transcript":spoken,"spoken_subscribe_count":1,
     "spoken_like_count":1,"similarity_to_script":round(similarity,3)
   },ensure_ascii=False,indent=2))
   return wav,probe_duration(wav)
  except Exception as e:
   print("ONE_TAKE_RETRY",attempt+1,str(e)[:200],flush=True)
   if attempt==2:raise
   time.sleep(6*(attempt+1))

def wrap(d,text,size,maxw=625):
 output=[];s=""
 for word in text.split():
  trial=(s+" "+word).strip()
  if d.textbbox((0,0),trial,font=font(size))[2]<=maxw:s=trial
  else:
   if s:output.append(s)
   s=word
 if s:output.append(s)
 return output
def cover_image(path,idx):
 src=Image.open(path).convert("RGB")
 # photographic center crop with slow pan/zoom, avoid distorting the actual product.
 size=(800,800)
 im=ImageOps.fit(src,size,method=Image.Resampling.LANCZOS,centering=(0.49 if idx%2==0 else 0.58,0.50))
 out=OUT/f"photo_scene_{idx:02}.jpg"
 im.save(out,quality=92);return out
def panel(idx,caption,outro=False):
 im=Image.new("RGBA",(W,H),(0,0,0,0))
 d=ImageDraw.Draw(im)
 title="#172F36";accent="#B94B38";text="#233039"
 if outro:
  d.rectangle((0,0,W,H),fill="#F7F3EE")
  d.rounded_rectangle((38,120,682,1140),radius=37,fill="#EEE4DC")
  d.text((360,343),"생활알고리즘",font=font(74),fill=title,anchor="mm")
  d.text((360,472),"알아두면 좋은 안전 상식",font=font(32),fill="#6D6661",anchor="mm")
  d.rounded_rectangle((57,633,663,826),radius=37,fill=accent)
  d.text((360,727),"구독과 좋아요",font=font(67),fill="white",anchor="mm")
  d.text((360,1020),"안전한 일상을 위한 1분 정보",font=font(31),fill=text,anchor="mm")
 else:
  d.rectangle((0,0,W,240),fill="#F7F3EE")
  d.rounded_rectangle((27,30,290,96),radius=21,fill=title)
  d.text((158,64),"생활알고리즘",font=font(37),fill="white",anchor="mm")
  d.text((687,68),"SAFETY",font=font(23),fill=accent,anchor="rm")
  d.text((360,166),"전기 모기채, 손이 닿으면?",font=font(47),fill=title,anchor="mm")
  d.rectangle((0,865,W,H),fill="#F7F3EE")
  d.rounded_rectangle((28,884,692,1173),radius=30,fill="#EAE1D8")
  d.rounded_rectangle((57,911,210,966),radius=17,fill=accent)
  d.text((133,939),f"POINT {idx+1:02d}",font=font(23),fill="white",anchor="mm")
  size=44;lines=wrap(d,caption,size)
  if len(lines)>3:size=37;lines=wrap(d,caption,size)
  y=1050-(len(lines)-1)*61/2
  for j,ln in enumerate(lines[:3]):
   d.text((360,y+j*61),ln,font=font(size),fill=text,anchor="mm")
  d.text((360,1220),"실제 사진 · 안전정보 · 직접 감전 실험 금지",font=font(24),fill="#84746D",anchor="mm")
 path=OUT/f"overlay_{idx:02}.png";im.save(path);return path

def print_time(s):
 n=round(s*1000);h,n=divmod(n,3600000);m,n=divmod(n,60000);sec,ms=divmod(n,1000)
 return f"{h:02}:{m:02}:{sec:02},{ms:03}"
def main():
 assets=download_photos()
 insect_video=download_insect_video()
 raw_voice,total=audio_generate()
 # Continuous narration: scene split by estimated spoken syllables, with a longer last CTA.
 weights=[len(line.replace(" ",""))+3 for line,_,_ in LINES]
 periods=[total*w/sum(weights) for w in weights]
 # Normalize times to the exact continuous audio duration
 periods[-1]+=total-sum(periods)
 media=[];timings=[];clock=0.
 for i,((spoken,caption,kind),dur) in enumerate(zip(LINES,periods)):
  overlay=panel(i,caption,kind=="outro")
  scene=OUT/f"scene_{i:02}.mp4"
  if kind=="outro":
   run("-f","lavfi","-i","color=c=0xf7f3ee:s=720x1280:r=30",
       "-loop","1","-framerate","30","-i",overlay,
       "-filter_complex","[0:v][1:v]overlay=0:0:shortest=1[v]",
       "-map","[v]","-t",f"{dur:.4f}",
       "-c:v","libx264","-preset","veryfast","-crf","24","-pix_fmt","yuv420p",scene)
  else:
   photo=assets[kind][i%len(assets[kind])]
   # Inject actual moving insect footage on one of the mosquito scenes, if available.
   if insect_video is not None and kind=="mosquito" and i==5:
    run("-stream_loop","-1","-i",insect_video,"-loop","1","-framerate","30","-i",overlay,
        "-filter_complex",
        "[0:v]scale=720:720:force_original_aspect_ratio=increase,crop=720:720,pad=720:1280:0:240:color=0xf7f3ee,fps=30[real];"
        "[real][1:v]overlay=0:0:shortest=1[v]",
        "-map","[v]","-t",f"{dur:.4f}","-c:v","libx264",
        "-preset","veryfast","-crf","25","-pix_fmt","yuv420p",scene)
   else:
    p=cover_image(photo,i)
    run("-loop","1","-framerate","30","-i",p,"-loop","1","-framerate","30","-i",overlay,
       "-filter_complex",
       "[0:v]zoompan=z='min(zoom+0.001,1.20)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=720x720:fps=30,"
       "pad=720:1280:0:240:color=0xf7f3ee[photomotion];"
       "[photomotion][1:v]overlay=0:0:shortest=1[v]",
       "-map","[v]","-t",f"{dur:.4f}","-c:v","libx264",
       "-preset","veryfast","-crf","25","-pix_fmt","yuv420p",scene)
  media.append(scene);timings.append((clock,clock+dur,spoken));clock+=dur
  print("RENDERED",i+1,"seconds",round(dur,2),flush=True)
 lst=OUT/"concat.txt";lst.write_text("".join(f"file '{p.name}'\n" for p in media))
 silent=OUT/"movie_silent.mp4"
 run("-f","concat","-safe","0","-i",lst,"-c","copy",silent)
 final=OUT/"electric_swatter_REAL_SINGLE_VOICE.mp4"
 run("-i",silent,"-i",raw_voice,"-map","0:v","-map","1:a",
     "-c:v","copy","-c:a","aac","-b:a","128k","-t",f"{total:.4f}",
     "-movflags","+faststart",final)
 (OUT/"captions.srt").write_text("\n".join(
  f"{i+1}\n{print_time(a)} --> {print_time(b)}\n{line}\n" for i,(a,b,line) in enumerate(timings)),encoding="utf-8")
 (OUT/"script.txt").write_text(SCRIPT,encoding="utf-8")
 (OUT/"sources.txt").write_text("OFFICIAL SAFETY\n"+"\n".join(SOURCES)+
   "\n\nPHOTOGRAPHIC MATERIAL\n"+(OUT/"photo_credits.txt").read_text()+
   ("\nACTUAL INSECT FOOTAGE "+VIDEO_SOURCE if insect_video else "\nNo video b-roll: actual photos animated with slow zoom"),
   encoding="utf-8")
 (OUT/"qa.json").write_text(json.dumps({
   "length_seconds":round(total,2),"voice_single_take":True,
   "cta_in_body_written":0,"cta_in_final_written":1,
   "audio_asr_verified_single_cta":True,
   "visual_material":"Actual licensed photos with moving Ken Burns; optional real insect footage",
   "actual_video_broll_included":bool(insect_video),
   "electric_swatter_photos":len(assets["swatter"]),
   "mosquito_photos":len(assets["mosquito"]),
   "youtube_published":False
 },ensure_ascii=False,indent=2),encoding="utf-8")
 assert final.stat().st_size>600000
 print("FINAL_VERIFIED",str(final),"DURATION",round(total,2),"BYTES",final.stat().st_size,flush=True)
if __name__=="__main__":main()
