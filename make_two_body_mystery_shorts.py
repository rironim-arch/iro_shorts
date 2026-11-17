"""Two curiosity-first 생활알고리즘 real-media Shorts. Reveal mystery only near mid-video; verified uninterrupted Charon narration with final-only CTA."""
import os,re,io,json,time,wave,subprocess,difflib
from pathlib import Path
import requests
import numpy as np
import imageio_ffmpeg
from PIL import Image,ImageFont,ImageDraw,ImageOps
from google import genai
from google.genai import types

ROOT=Path("body_mysteries_shorts");ROOT.mkdir(exist_ok=True)
FF=imageio_ffmpeg.get_ffmpeg_exe()
CLIENT=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
R=requests.Session();R.headers.update({"User-Agent":"Mozilla/5.0"})
CONFIG={
 "sleep": {
  "title": "잠들다 몸이 움찔? 왜?",
  "accent": "#5B75A0",
  "name": "수면의 미스터리",
  "lines": [
   [
    "잠들기 직전, 갑자기 바닥이 꺼지는 느낌에 온몸이 움찔! 이런 경험 있으시죠?",
    "잠들다 바닥이 꺼지는 느낌?!"
   ],
   [
    "눈을 떠보면 침대는 그대로인데, 심장은 철렁하고 잠이 확 달아납니다.",
    "침대는 그대로인데 왜?"
   ],
   [
    "왜 하필 잠에 빠지려는 바로 그 순간, 몸이 혼자 움직이는 걸까요?",
    "몸이 혼자 움직이는 이유"
   ],
   [
    "이 현상의 이름은 입면 경련. 잠드는 과정에서 근육이 순간적으로 수축하는 겁니다.",
    "정체 공개 · 입면 경련"
   ],
   [
    "높은 곳에서 떨어지는 듯한 느낌이 함께 나타나기도 하죠.",
    "떨어지는 듯한 감각"
   ],
   [
    "정확한 발생 원인은 아직 하나로 밝혀지지 않았습니다.",
    "정확한 원인은 아직 연구 중"
   ],
   [
    "스트레스가 심하거나 잠이 부족할 때, 카페인을 늦게 마셨을 때 더 자주 느낄 수 있어요.",
    "스트레스 · 수면 부족 · 카페인"
   ],
   [
    "가끔 나타나는 건 대체로 큰 문제가 없지만, 잠을 계속 방해할 만큼 잦다면 진료를 받아보세요.",
    "자주 잠을 방해한다면 진료"
   ],
   [
    "기억해둘 만했다면 구독과 좋아요! 생활알고리즘.",
    "구독과 좋아요"
   ]
  ],
  "videos": [30285724,6753821,8410558,6753819,8410546,9355003],
  "photos": [6943445,6753355,7505059,5867015,8057109,7445246],
  "src": [
   "https://health.clevelandclinic.org/why-do-i-feel-like-im-falling-when-im-falling-asleep-video",
   "https://www.sleepfoundation.org/parasomnias/hypnic-jerks"
  ],
  "filename": "sleep_falling_sensation_hypnic_jerk.mp4",
  "description": "잠들기 직전 바닥이 꺼지는 듯한 느낌에 갑자기 온몸이 움찔한 적 있으신가요? 정체를 바로 말하지 않고, 실제로 몸에서 일어나는 변화와 잠을 방해하는 요인을 풀어드립니다. Cleveland Clinic 등 의학 자료를 참고했습니다. 증상이 잦거나 수면을 심하게 방해하면 진료를 받아보세요.\n#입면경련 #자다가움찔 #수면상식 #잠잘때떨어지는느낌 #생활알고리즘 #shorts"
 },
 "eyes": {
  "title": "눈앞에 떠다니는 검은 점?",
  "accent": "#46878A",
  "name": "눈 건강 · 의외의 사실",
  "lines": [
   [
    "눈앞에 검은 점 하나가 둥둥 떠다닙니다. 손을 뻗어도 절대 잡히지 않죠.",
    "잡히지 않는 검은 점?!"
   ],
   [
    "눈을 돌리면 따라오고, 정면으로 보려고 하면 슬쩍 피해 버립니다.",
    "눈을 돌리면 따라온다"
   ],
   [
    "특히 하얀 벽이나 맑은 하늘에서 더 또렷해지는데, 대체 정체가 뭘까요?",
    "밝은 곳에서 더 잘 보이는 이유"
   ],
   [
    "놀랍게도 범인은 눈 밖이 아니라 눈 안에 있습니다. 바로 비문증입니다.",
    "정체 공개 · 비문증"
   ],
   [
    "눈 속 유리체의 작은 뭉침이 망막에 그림자를 만들어 점이나 실처럼 보여요.",
    "눈 속 작은 뭉침의 그림자"
   ],
   [
    "오래 보이던 점이 별 변화 없이 유지되는 건 흔한 현상일 수 있습니다.",
    "예전부터 같다면 흔한 현상일 수도"
   ],
   [
    "하지만 갑자기 수가 늘거나 번쩍이는 빛이 함께 보인다면 이야기가 달라집니다.",
    "갑자기 늘거나 번쩍인다면?"
   ],
   [
    "시야에 검은 커튼 같은 그림자가 생기면 망막이 찢어지거나 떨어지는 신호일 수 있어요. 즉시 안과 진료가 필요합니다.",
    "검은 커튼 · 번쩍임 → 즉시 진료"
   ],
   [
    "도움이 되셨다면 구독과 좋아요! 생활알고리즘.",
    "구독과 좋아요"
   ]
  ],
  "videos": [
   5252983,
   9808079,
   7248407,
   40481915,
   8075759,
   3327253,
   7120150,
   6565832
  ],
  "photos": [
   28491940,
   9929043,
   9930771,
   9882541,
   16786434
  ],
  "src": [
   "https://www.nei.nih.gov/eye-health-information/eye-conditions-and-diseases/floaters",
   "https://www.nei.nih.gov/eye-health-information/eye-conditions-and-diseases/retinal-detachment",
   "https://www.nhs.uk/symptoms/floaters-and-flashes-in-the-eyes/"
  ],
  "filename": "black_dots_in_vision_eye_floaters.mp4",
  "description": "눈앞을 따라다니는 검은 점! 하얀 벽을 보면 더 선명해진다면 정체가 뭘까요? 비문증과 함께 절대 놓치면 안 되는 망막 이상 신호까지 미국 국립안연구소(NEI)와 NHS 자료로 알려드립니다. 갑자기 점이 늘고 번쩍임이나 시야를 가리는 그림자가 나타나면 즉시 안과 진료를 받으세요.\n#비문증 #눈앞검은점 #날파리증 #안과건강 #생활알고리즘 #shorts"
 }
}
for k,v in CONFIG.items():
 assert len(v["lines"])==9
 assert sum("구독과 좋아요" in a for a,b in v["lines"])==1
 assert all("구독" not in a+b and "좋아요" not in a+b for a,b in v["lines"][:-1])

def ff(*args,timeout=160):
 subprocess.run([FF,"-y","-hide_banner","-loglevel","error",*map(str,args)],check=True,timeout=timeout)
def probed(path):
 a=subprocess.run([FF,"-hide_banner","-i",str(path)],capture_output=True,text=True,timeout=18)
 return "Video:" in a.stderr and "Duration:" in a.stderr
def fontfile():
 for p in ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
           "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
           "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"):
  if Path(p).exists():return p
 p=ROOT/"NanumGothic-Bold.ttf"
 if not p.exists():
  r=R.get("https://raw.githubusercontent.com/google/fonts/main/ofl/nanumgothic/NanumGothic-Bold.ttf",timeout=30)
  r.raise_for_status();p.write_bytes(r.content)
 return str(p)
FONT=fontfile()
def f(sz):return ImageFont.truetype(FONT,sz)

def getphoto(id,p):
 try:
  u=f"https://images.pexels.com/photos/{id}/pexels-photo-{id}.jpeg?auto=compress&cs=tinysrgb&w=1100"
  r=R.get(u,timeout=(6,25));r.raise_for_status()
  im=Image.open(io.BytesIO(r.content)).convert("RGB")
  if min(im.size)<300:return None
  im.save(p,quality=90)
  print("PHOTO",id,"OK",flush=True);return p
 except Exception as e:
  print("PHOTO",id,"ERROR",str(e)[:90],flush=True);return None

def getvideo(id,p):
 urls=[f"https://www.pexels.com/video/download/{id}/"]
 for fps in (24,25,30,50,60):
  for dim in ("720_1280","1280_720","960_540","540_960","1920_1080","1080_1920"):
   urls.append(f"https://videos.pexels.com/video-files/{id}/{id}-hd_{dim}_{fps}fps.mp4")
 for k,url in enumerate(urls):
  try:
   if k>0:
    h=R.head(url,timeout=2.5)
    if h.status_code!=200 or "video" not in h.headers.get("content-type","").lower():continue
    if int(h.headers.get("content-length","0") or "0")>70000000:continue
   with R.get(url,stream=True,timeout=(6,40)) as resp:
    resp.raise_for_status()
    ct=resp.headers.get("content-type","").lower()
    if "video" not in ct and "octet" not in ct:continue
    size=0
    with p.open("wb") as out:
     for buf in resp.iter_content(512*1024):
      if buf:
       size+=len(buf)
       if size>75_000_000:raise ValueError("oversized clip")
       out.write(buf)
   if p.stat().st_size>150000 and probed(p):
    print("VIDEO",id,"OK",p.stat().st_size,flush=True);return p
  except Exception:pass
  p.unlink(missing_ok=True)
 print("VIDEO",id,"UNAVAILABLE",flush=True);return None

def media(key,cfg):
 vids=[];photos=[];credits=[]
 for id in cfg["videos"]:
  if len(vids)>=3:break
  p=ROOT/f"{key}_video_{id}.mp4"
  if getvideo(id,p):
   vids.append(p);credits.append(f"Video Pexels License: https://www.pexels.com/video/{id}/")
 for id in cfg["photos"]:
  if len(photos)>=(5 if key=="sleep" else 3):break
  p=ROOT/f"{key}_photo_{id}.jpg"
  if getphoto(id,p):
   photos.append(p);credits.append(f"Photo Pexels License: https://www.pexels.com/photo/{id}/")
 if not vids:raise RuntimeError("Could not secure real video footage for "+key)
 if not photos:raise RuntimeError("Could not secure real photos for "+key)
 (ROOT/f"{key}_sources.txt").write_text("\n".join(cfg["src"])+
  "\n\nStock license sources\n"+"\n".join(credits)+"\nhttps://www.pexels.com/license/",encoding="utf-8")
 return vids,photos
def normalized(s):return re.sub(r"[^A-Za-z0-9가-힣]","",s)
def wavlen(p):
 with wave.open(str(p),"rb") as w:return w.getnframes()/w.getframerate()
def voice(key,cfg):
 script="\n".join(line for line,caption in cfg["lines"])
 for attempt in range(4):
  try:
   prompt=("Speak the complete Korean narration below as ONE continuous male Charon voice recording. "
      "Keep the SAME voice and tone through the entire narration. Calm, engaging, clear and natural. "
      "Read only the words as written. Do not add any greeting, slogan, call-to-action, or words. "
      "Read all paragraphs in order, with slight pauses. Don't read delimiters. "
      "Narration only, no sound effects.\n\n===START===\n"+script+"\n===END===")
   res=CLIENT.models.generate_content(
    model="gemini-2.5-flash-preview-tts",contents=prompt,
    config=types.GenerateContentConfig(response_modalities=["AUDIO"],
     speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
      prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
   blob=next((p.inline_data for p in res.candidates[0].content.parts
              if p.inline_data and p.inline_data.data),None)
   if blob is None:raise RuntimeError("No audio data")
   raw=ROOT/f"{key}_single_take.wav"
   if blob.data.startswith(b"RIFF"):raw.write_bytes(blob.data)
   else:
    m=re.search(r"rate=(\d+)",blob.mime_type or "")
    with wave.open(str(raw),"wb") as wf:
     wf.setnchannels(1);wf.setsampwidth(2)
     wf.setframerate(int(m.group(1)) if m else 24000)
     wf.writeframes(blob.data)
   if not 24<wavlen(raw)<120:raise RuntimeError("Invalid audio duration")
   recognized=CLIENT.models.generate_content(
    model="gemini-3.8-flash",
    contents=["오디오에서 실제로 들리는 모든 한국어 말을 빠짐없이 받아쓰세요. 오디오에 없는 말을 추가하지 마세요.",
      types.Part.from_bytes(data=raw.read_bytes(),mime_type="audio/wav")])
   actual=(recognized.text or "").strip()
   norm=normalized(actual)
   cta=norm.count("구독")==1 and norm.count("좋아요")==1
   similarity=difflib.SequenceMatcher(None,normalized(script),norm).ratio()
   print(key,"VOICE_QA",attempt+1,round(similarity,3),"CTA_ONE",cta,flush=True)
   print(key,"ACTUAL_AUDIO_WORDS",actual,flush=True)
   if not cta or similarity<0.82:raise RuntimeError("TTS hallucination / repeated CTA")
   sped=ROOT/f"{key}_charon_125.wav"
   ff("-i",raw,"-af","atempo=1.25","-ar","24000","-ac","1",sped)
   seconds=wavlen(sped)
   (ROOT/f"{key}_voice_QA.json").write_text(json.dumps({
    "single_take":True,"voice":"Gemini Charon","speed":1.25,
    "actual_transcript":actual,"script":script,
    "cta_subscribe_count":1,"cta_like_count":1,
    "duration_seconds":round(seconds,2),"similarity":round(similarity,3)
   },ensure_ascii=False,indent=2),encoding="utf-8")
   return sped,seconds
  except Exception as e:
   print(key,"VOICE_RETRY",attempt+1,str(e)[:180],flush=True)
   if attempt==3:raise
   time.sleep(5*(attempt+1))
def wrap(draw,text,sz,maxwidth=642):
 words=text.split();lines=[];line=""
 for w in words:
  nxt=(line+" "+w).strip()
  if draw.textbbox((0,0),nxt,font=f(sz))[2]<=maxwidth:line=nxt
  else:
   if line:lines.append(line)
   line=w
 if line:lines.append(line)
 return lines

def overlay(key,cfg,i,caption,ending):
 canvas=Image.new("RGBA",(720,1280),(0,0,0,0))
 d=ImageDraw.Draw(canvas);ink="#29313C";cream="#FCF7EF";accent=cfg["accent"]
 if ending:
  d.rectangle((0,0,720,1280),fill=cream)
  d.rounded_rectangle((31,70,689,1191),radius=48,fill="#EEE2D5")
  d.text((360,266),"생활알고리즘",font=f(76),fill=ink,anchor="mm")
  d.text((360,438),"알아두면 좋은 생활정보",font=f(38),fill=accent,anchor="mm")
  d.rounded_rectangle((60,635,660,829),radius=35,fill=accent)
  d.text((360,729),"구독과 좋아요",font=f(68),fill="white",anchor="mm")
  d.text((360,1025),"내일도 유용한 정보로!",font=f(34),fill=ink,anchor="mm")
 else:
  d.rectangle((0,0,720,264),fill=cream)
  d.rounded_rectangle((26,26,284,103),radius=22,fill=ink)
  d.text((155,65),"생활알고리즘",font=f(35),fill="white",anchor="mm")
  d.text((692,63),cfg["name"],font=f(22),fill=accent,anchor="rm")
  d.text((360,185),cfg["title"],font=f(43),fill=ink,anchor="mm")
  d.rectangle((0,925,720,1280),fill=cream)
  d.rounded_rectangle((26,944,694,1169),radius=32,fill="#EFE5DB")
  d.rounded_rectangle((52,960,145,1010),radius=16,fill=accent)
  d.text((98,985),f"{i+1:02}",font=f(26),fill="white",anchor="mm")
  sz=45;lines=wrap(d,caption,sz)
  if len(lines)>2:sz=38;lines=wrap(d,caption,sz)
  y=1082-(len(lines)-1)*60/2
  for j,ln in enumerate(lines[:3]):
   d.text((360,y+j*60),ln,font=f(sz),fill=ink,anchor="mm")
  d.text((360,1216),"궁금증 뒤에 숨은 과학",font=f(26),fill="#80776D",anchor="mm")
 p=ROOT/f"{key}_overlay_{i:02}.png";canvas.save(p);return p

def durations(voicepath,cfg,total):
 lens=[len(normalized(a))+1 for a,b in cfg["lines"]]
 cuts=np.cumsum(lens)[:-1]/sum(lens)*total
 with wave.open(str(voicepath),"rb") as w:
  sr=w.getframerate()
  x=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)
 hop=max(1,int(sr*.05));n=len(x)//hop
 powers=np.sqrt(np.mean(x[:n*hop].reshape(n,hop)**2,axis=1))
 borders=[0.]
 for goal in cuts:
  low=max(0,int((goal-.55)/.05));high=min(n,int((goal+.55)/.05))
  if high>low:
   ix=np.arange(low,high)
   scores=powers[low:high]+abs(ix*.05-goal)*float(np.percentile(powers,65))*.26
   actual=float(ix[int(np.argmin(scores))]*.05)
  else:actual=float(goal)
  borders.append(max(borders[-1]+.8,min(actual,total-1)))
 borders.append(total)
 return [max(.3,borders[i+1]-borders[i]) for i in range(len(borders)-1)]
def stamp(t):
 n=round(t*1000);h,n=divmod(n,3600000);m,n=divmod(n,60000);s,ms=divmod(n,1000)
 return f"{h:02}:{m:02}:{s:02},{ms:03}"
def render(key,cfg):
 realvideo,realphotos=media(key,cfg)
 wav,total=voice(key,cfg)
 span=durations(wav,cfg,total)
 print(key,"DURATION",round(total,2),"CLIPS",len(realvideo),"PHOTOS",len(realphotos),flush=True)
 scenes=[];srt=[];cursor=0
 for i,((text,caption),seconds) in enumerate(zip(cfg["lines"],span)):
  closing=i==len(cfg["lines"])-1
  png=overlay(key,cfg,i,caption,closing)
  scene=ROOT/f"{key}_scene_{i:02}.mp4"
  if closing:
   ff("-f","lavfi","-i","color=c=0xfcf7ef:s=720x1280:r=30",
      "-loop","1","-framerate","30","-i",png,
      "-filter_complex","[0:v][1:v]overlay=0:0:shortest=1[v]",
      "-map","[v]","-t",f"{seconds:.3f}",
      "-c:v","libx264","-preset","veryfast","-crf","26","-pix_fmt","yuv420p",scene)
  elif (key=="sleep" and i in (0,2,4,6)) or (key!="sleep" and i%4==2):
   img=ImageOps.fit(Image.open(realphotos[i%len(realphotos)]).convert("RGB"),(800,760))
   jpg=ROOT/f"{key}_crop_{i:02}.jpg";img.save(jpg,quality=88)
   ff("-loop","1","-framerate","30","-i",jpg,
      "-loop","1","-framerate","30","-i",png,
      "-filter_complex","[0:v]zoompan=z='min(zoom+0.0008,1.14)':"
      "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=720x660:fps=30,"
      "pad=720:1280:0:264:color=0xfcf7ef[real];"
      "[real][1:v]overlay=0:0:shortest=1[v]",
      "-map","[v]","-t",f"{seconds:.3f}",
      "-c:v","libx264","-preset","veryfast","-crf","27","-pix_fmt","yuv420p",scene)
  else:
   clip=realvideo[(i//2)%len(realvideo)]
   ff("-stream_loop","-1","-i",clip,
      "-loop","1","-framerate","30","-i",png,
      "-filter_complex","[0:v]scale=720:660:force_original_aspect_ratio=increase,"
      "crop=720:660,pad=720:1280:0:264:color=0xfcf7ef,fps=30[real];"
      "[real][1:v]overlay=0:0:shortest=1[v]",
      "-map","[v]","-t",f"{seconds:.3f}",
      "-c:v","libx264","-preset","veryfast","-crf","27","-pix_fmt","yuv420p",scene)
  scenes.append(scene);srt.append((cursor,cursor+seconds,text));cursor+=seconds
  print(key,"SCENE_DONE",i+1,round(seconds,2),flush=True)
 listfile=ROOT/f"{key}_concat.txt"
 listfile.write_text("".join(f"file '{p.name}'\n" for p in scenes),encoding="utf-8")
 silent=ROOT/f"{key}_silent.mp4"
 ff("-f","concat","-safe","0","-i",listfile,"-c","copy",silent)
 final=ROOT/cfg["filename"]
 ff("-i",silent,"-i",wav,"-map","0:v:0","-map","1:a:0",
    "-c:v","copy","-c:a","aac","-b:a","112k","-t",f"{total:.3f}",
    "-movflags","+faststart",final)
 (ROOT/f"{key}_captions.srt").write_text("\n".join(
  f"{i+1}\n{stamp(a)} --> {stamp(b)}\n{line}\n" for i,(a,b,line) in enumerate(srt)),encoding="utf-8")
 (ROOT/f"{key}_script.txt").write_text("\n".join(x for x,c in cfg["lines"]),encoding="utf-8")
 (ROOT/f"{key}_metadata.json").write_text(json.dumps({
  "title":cfg["title"]+" #shorts","description":cfg["description"],
  "duration_seconds":round(total,2),
  "voice":"single Charon narration 1.25x",
  "body_cta_count":0,"final_cta_count":1,
  "actual_voice_transcript_verified":True,
  "real_clips_count":len(realvideo),"real_photos_count":len(realphotos),
  "sources":cfg["src"],"youtube_uploaded":False
 },ensure_ascii=False,indent=2),encoding="utf-8")
 assert final.stat().st_size>600000
 print("DELIVERABLE_READY",key,final,"BYTES",final.stat().st_size,flush=True)

if __name__=="__main__":
 for n in ["sleep","eyes"]:
  render(n,CONFIG[n])
 print("BODY_MYSTERY_BOTH_VERIFIED",flush=True)
