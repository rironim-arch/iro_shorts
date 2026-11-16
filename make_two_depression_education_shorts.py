"""Create two Korean 9:16 Shorts with real Pexels B-roll and a single verified Charon take each."""
import os,re,io,json,time,wave,subprocess,difflib
from pathlib import Path
import requests
import numpy as np
import imageio_ffmpeg
from PIL import Image,ImageFont,ImageDraw,ImageOps
from google import genai
from google.genai import types

ROOT=Path("mental_health_shorts_exports");ROOT.mkdir(exist_ok=True)
FF=imageio_ffmpeg.get_ffmpeg_exe()
CLIENT=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
R=requests.Session();R.headers.update({"User-Agent":"Mozilla/5.0"})
CONFIG={
 "cause": {
  "title": "우울증은 왜 생기는 걸까?",
  "accent": "#806087",
  "name": "마음 건강",
  "lines": [
   [
    "특별히 큰 문제가 없는데도 우울증이 생길 수 있을까요? 돈도 있고, 가족도 있는데 왜 마음이 무너질까요?",
    "별일 없는데 우울증이 생긴다?"
   ],
   [
    "세계보건기구는 우울증에 하나의 원인만 있는 게 아니라고 설명합니다.",
    "우울증 원인은 하나가 아니다"
   ],
   [
    "유전적 요인과 뇌의 기능, 심리 상태, 스트레스와 생활 환경이 복합적으로 작용할 수 있죠.",
    "유전 · 생물학 · 스트레스 · 환경"
   ],
   [
    "수면 문제나 외로움, 질병 같은 상황도 우울증 위험에 영향을 줄 수 있습니다.",
    "수면 · 고립 · 질병도 관련"
   ],
   [
    "중요한 건 단순히 마음이 약해서 생기는 병이 아니라는 사실입니다.",
    "의지가 약해서 생기는 병이 아니다"
   ],
   [
    "그렇다고 기분이 하루 이틀 가라앉았다고 모두 우울증은 아닙니다.",
    "일시적 우울감과는 다르다"
   ],
   [
    "우울한 기분이나 흥미 상실이 거의 매일 이 주 이상 이어지고 일상까지 힘들어진다면 전문가 평가가 필요할 수 있어요.",
    "2주 이상 지속되면 전문 상담 고려"
   ],
   [
    "우울증에는 상담과 약물치료 등 효과적인 치료 방법이 있습니다.",
    "도움받고 치료할 수 있다"
   ],
   [
    "도움이 되셨다면 구독과 좋아요! 생활알고리즘.",
    "구독과 좋아요"
   ]
  ],
  "videos": [
   6756338,
   8731296,
   6614775,
   35215455,
   4928383,
   5698957
  ],
  "photos": [
   7654802,
   7176052,
   7278919,
   7176056,
   7260462
  ],
  "src": [
   "https://www.who.int/news-room/fact-sheets/detail/depression",
   "https://www.nimh.nih.gov/health/topics/depression",
   "https://www.nimh.nih.gov/health/publications/depression",
   "https://health.kdca.go.kr/healthinfo/biz/health/gnrlzHealthInfo/gnrlzHealthInfo/gnrlzHealthInfoView.do?cntnts_sn=6788"
  ],
  "filename": "why_depression_happens.mp4",
  "description": "별일 없는데도 우울증이 생길 수 있을까요? 우울증은 의지 부족이나 단일한 호르몬 문제로 설명되지 않습니다. WHO, NIMH, 질병관리청 공식 자료를 바탕으로 유전·생물학·스트레스·생활 환경 등 다양한 요인과 도움받아야 할 신호를 알아봅니다.\n#우울증원인 #마음건강 #심리학 #우울감 #생활알고리즘 #shorts"
 },
 "signs": {
  "title": "우울증에 걸리면 꼭 슬퍼 보일까?",
  "accent": "#467C85",
  "name": "심리 · 건강",
  "lines": [
   [
    "매일 사람들과 웃으며 출근하는 사람. 그런데도 우울증이 있을 수 있을까요?",
    "웃는 사람도 우울증일 수 있다?"
   ],
   [
    "그렇습니다. 우울증이 있다고 항상 울거나 슬퍼 보이는 것은 아닙니다.",
    "겉모습만으로 알 수 없다"
   ],
   [
    "예전에는 즐거웠던 일이 더는 재미없고, 좋아하던 취미에도 흥미가 사라질 수 있죠.",
    "좋아하던 일이 즐겁지 않다"
   ],
   [
    "잠이 너무 많아지거나 반대로 잠들기 어렵고, 식욕이나 집중력이 달라질 수도 있습니다.",
    "수면 · 식욕 · 집중력 변화"
   ],
   [
    "짜증이 늘거나 에너지가 너무 부족해 평소 하던 일도 버거울 수 있어요.",
    "무기력과 짜증도 나타날 수 있다"
   ],
   [
    "하지만 이런 증상 하나만으로 우울증이라고 단정해선 안 됩니다.",
    "증상 하나로 자가진단 금지"
   ],
   [
    "우울감이나 흥미 상실이 거의 매일 이 주 이상 이어지고 일상에 지장을 준다면 전문가와 상담해 보세요.",
    "2주 이상 · 일상생활 지장"
   ],
   [
    "우울증은 치료할 수 있습니다. 겉으로 웃는다고 마음까지 괜찮다고 단정하지 마세요.",
    "웃는 얼굴만 보고 단정하지 말자"
   ],
   [
    "도움이 되셨다면 구독과 좋아요! 생활알고리즘.",
    "구독과 좋아요"
   ]
  ],
  "videos": [
   3253967,
   8279412,
   8731296,
   6614775,
   6756338,
   5698957
  ],
  "photos": [
   7490841,
   7278919,
   7176055,
   7654802,
   7267090
  ],
  "src": [
   "https://www.who.int/news-room/fact-sheets/detail/depression",
   "https://www.nimh.nih.gov/health/publications/depression",
   "https://health.kdca.go.kr/healthinfo/biz/health/gnrlzHealthInfo/gnrlzHealthInfo/gnrlzHealthInfoView.do?cntnts_sn=6788"
  ],
  "filename": "depression_not_always_sad.mp4",
  "description": "매일 웃고 출근하는 사람도 우울증을 겪을 수 있을까요? 우울증은 슬픔뿐 아니라 흥미 상실·수면·식욕·집중력 변화로 나타날 수 있습니다. WHO와 질병관리청 공식 자료를 바탕으로 우울감과 우울증의 차이, 도움받아야 할 신호를 알아봅니다.\n※ 이 영상은 일반적인 건강정보이며 개인의 진단을 대신하지 않습니다.\n#우울증증상 #마음건강 #심리 #우울증 #생활알고리즘 #shorts"
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
 for fps in (24,25,30,50):
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
  if len(photos)>=3:break
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
   if not 22<wavlen(raw)<110:raise RuntimeError("Invalid audio duration")
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
  d.text((360,1216),"마음까지 이해하는 생활정보",font=f(26),fill="#80776D",anchor="mm")
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
  elif i%4==2:
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
 for n in ["cause","signs"]:
  render(n,CONFIG[n])
 print("BOTH_MENTAL_HEALTH_SHORTS_PASSED",flush=True)
