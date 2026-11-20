"""Two curiosity-first 생활알고리즘 real-media Shorts. Reveal mystery only near mid-video; verified uninterrupted Charon narration with final-only CTA."""
import os,re,io,json,time,wave,subprocess,difflib
from pathlib import Path
import requests
import numpy as np
import imageio_ffmpeg
from PIL import Image,ImageFont,ImageDraw,ImageOps
from google import genai
from google.genai import types

ROOT=Path("bathroom_cleaner_exports");ROOT.mkdir(exist_ok=True)
FF=imageio_ffmpeg.get_ffmpeg_exe()
CLIENT=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
R=requests.Session();R.headers.update({"User-Agent":"Mozilla/5.0"})
CONFIG={
 "bathroom": {
  "title": "청소 중 갑자기 기침이 난다면?",
  "accent": "#F2C25E",
  "name": "생활 안전",
  "lines": [
   [
    "화장실을 청소하는데 갑자기 눈이 따갑고 목이 답답해집니다. 이런 적 있으신가요?",
    ""
   ],
   [
    "더 깨끗하게 하려고 평소처럼 세제를 쓴 것뿐인데, 왜 갑자기 기침이 나는 걸까요?",
    ""
   ],
   [
    "환기가 안 돼서일까요? 냄새가 독해서일까요? 그보다 먼저 확인할 것이 있습니다.",
    ""
   ],
   [
    "원인은 서로 다른 세정제를 함께 사용한 것일 수 있어요. 특히 락스와 다른 세제를 섞으면 위험한 가스가 생길 수 있습니다.",
    ""
   ],
   [
    "산성 성분이 든 일부 화장실 세정제와 락스가 만나면, 눈과 호흡기를 자극하는 염소가스가 발생할 수 있어요.",
    ""
   ],
   [
    "미국 질병통제예방센터는 락스를 다른 세정제나 소독제와 절대로 섞지 말라고 경고합니다.",
    ""
   ],
   [
    "세정제는 한 번에 한 종류만 사용하고, 제품 설명을 지키며 창문을 열어 환기하세요.",
    ""
   ],
   [
    "청소 중 눈이 따갑거나 숨쉬기 힘들다면 즉시 그 자리를 벗어나 신선한 공기를 마시세요. 증상이 심하면 바로 119에 연락하세요.",
    ""
   ],
   [
    "청소할 때 꼭 기억하세요. 구독과 좋아요, 생활알고리즘.",
    ""
   ]
  ],
  "videos": [
   9472849,
   9472840,
   9472852,
   4238767,
   9472823,
   4238704,
   4145824
  ],
  "photos": [
   9462643,
   9462635,
   4239041,
   4239101,
   9462638,
   28576636,
   4098761,
   4239130
  ],
  "src": [
   "https://www.cdc.gov/hygiene/about/cleaning-and-disinfecting-with-bleach.html",
   "https://www.cdc.gov/chemical-emergencies/chemical-fact-sheets/chlorine.html",
   "https://www.poison.org/articles/chlorine-gas"
  ],
  "filename": "bathroom_cleaners_toxic_gas_safety.mp4",
  "description": "화장실 청소 중 갑자기 눈이 따갑고 기침이 날 때, 원인은 단순한 냄새가 아닐 수도 있습니다. 락스와 다른 세정제를 섞으면 위험한 가스가 발생할 수 있습니다. 미국 CDC와 Poison Control 공식 자료를 바탕으로 화장실 청소 안전수칙을 설명합니다. 세정제는 혼합하지 말고 제품 사용법을 따르며 충분히 환기하세요. 증상이 생기면 현장을 떠나 신선한 공기를 마시고, 호흡곤란 등 심한 증상은 119에 연락하세요.\n#락스 #화장실청소 #청소세제 #유독가스 #생활안전 #생활알고리즘 #shorts"
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
  if len(photos)>=5:break
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
def wrap(draw,text,sz,maxwidth=638):
 words=text.split();lines=[];line=""
 for w in words:
  nxt=(line+" "+w).strip()
  if draw.textbbox((0,0),nxt,font=f(sz))[2]<=maxwidth:line=nxt
  else:
   if line:lines.append(line)
   line=w
 if line:lines.append(line)
 return lines

def chunks(text,cap=21):
 """Keep phrases in spoken order for several on-screen caption changes per scene."""
 # Split on punctuation first and reflow by whitespace; never add text not spoken.
 words=text.replace(","," ,").replace("."," .").replace("?"," ?").replace("!"," !").split()
 parts=[];buf=[]
 for w in words:
  if w in (",",".","?","!"):
   if buf and w in (".","?","!"):
    parts.append(" ".join(buf)+w);buf=[]
   elif buf:
    buf[-1]+=w
   continue
  if buf and len(" ".join(buf+[w]))>cap:
   parts.append(" ".join(buf));buf=[]
  buf.append(w)
 if buf:parts.append(" ".join(buf))
 # Avoid 1-word flashes
 j=0
 while j<len(parts)-1:
  if len(parts[j])<7 or len(parts[j+1])<7:
   parts[j:j+2]=[parts[j]+" "+parts[j+1]]
  else:j+=1
 return parts or [text]

def header_png(key,cfg,i,closing=False):
 c=Image.new("RGBA",(720,1280),(0,0,0,0));d=ImageDraw.Draw(c)
 if closing:
  d.rectangle((0,0,720,1280),fill="#0D223A")
  d.text((360,320),"생활알고리즘",font=f(66),fill="#FFFFFF",anchor="mm")
  d.text((360,440),"세제 혼합 금지",font=f(59),fill="#F2C25E",anchor="mm")
  d.rounded_rectangle((65,685,655,836),radius=30,fill="#F2C25E")
  d.text((360,760),"구독과 좋아요",font=f(62),fill="#101E35",anchor="mm")
  d.text((360,1005),"안전한 습관을 함께",font=f(35),fill="white",anchor="mm")
 else:
  d.rectangle((0,0,720,172),fill="#0D223A")
  d.text((28,43),"생활알고리즘",font=f(30),fill="#FFFFFF",anchor="lm")
  d.text((690,43),cfg["name"],font=f(26),fill="#F2C25E",anchor="rm")
  d.text((360,107),cfg["title"],font=f(39),fill="#FFFFFF",anchor="mm")
  d.rectangle((30,165,690,172),fill="#C89D45")
  d.text((683,123),f"{i+1:02}",font=f(17),fill="#9EA9B9",anchor="rm")
 p=ROOT/f"{key}_header_{i:02}.png";c.save(p);return p

def caption_png(key,i,j,words):
 c=Image.new("RGBA",(720,1280),(0,0,0,0));d=ImageDraw.Draw(c)
 # Black transparent band is over real footage, NOT a separate bottom panel
 d.rounded_rectangle((18,868,702,1096),radius=23,fill=(0,0,0,166))
 size=51
 lines=wrap(d,words,size,626)
 while len(lines)>3 and size>36:
  size-=3;lines=wrap(d,words,size,626)
 spacing=size+12
 y=979-(len(lines)-1)*spacing/2
 for k,line in enumerate(lines):
  d.text((360,int(y+k*spacing)),line,font=f(size),fill="white",stroke_width=3,stroke_fill="#070B13",anchor="mm")
 p=ROOT/f"{key}_caption_{i:02}_{j:02}.png";c.save(p);return p

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
 for i,((script,caption),seconds) in enumerate(zip(cfg["lines"],span)):
  closing=i==len(cfg["lines"])-1
  hdr=header_png(key,cfg,i,closing)
  scene=ROOT/f"{key}_scene_{i:02}.mp4"
  if closing:
   ff("-f","lavfi","-i","color=c=0x0d223a:s=720x1280:r=30",
      "-loop","1","-framerate","30","-i",hdr,
      "-filter_complex","[0:v][1:v]overlay=0:0:shortest=1[v]",
      "-map","[v]","-t",f"{seconds:.3f}",
      "-c:v","libx264","-preset","veryfast","-crf","26","-pix_fmt","yuv420p",scene)
   srt.append((cursor,cursor+seconds,script))
  else:
   # Speak-aligned captions: replace actual caption text 2-4 times per scene.
   captions=chunks(script)
   lengths=[max(2,len(normalized(t))) for t in captions]
   borders=np.cumsum([0]+lengths)/sum(lengths)*seconds
   pictures=[caption_png(key,i,j,txt) for j,txt in enumerate(captions)]
   photo=i in (2,4,6)
   args=[]
   if photo:
    img=ImageOps.fit(Image.open(realphotos[{2:0,4:2,6:4}[i]%len(realphotos)]).convert("RGB"),(790,1230))
    jpg=ROOT/f"{key}_crop_{i:02}.jpg";img.save(jpg,quality=89)
    args+=["-loop","1","-framerate","30","-i",jpg]
    prep="[0:v]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,fps=30[bg];"
   else:
    clip=realvideo[{0:0,1:1,3:2,5:0,7:1}.get(i,0)%len(realvideo)]
    args+=["-stream_loop","-1","-i",clip]
    prep="[0:v]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,fps=30[bg];"
   args+=["-loop","1","-framerate","30","-i",hdr]
   for p in pictures:args+=["-loop","1","-framerate","30","-i",p]
   graph=prep+"[bg][1:v]overlay=0:0:shortest=1[v0];"
   for j,_ in enumerate(pictures):
    a=float(borders[j]);b=float(borders[j+1])
    graph+=f"[v{j}][{j+2}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})':shortest=1[v{j+1}];"
    srt.append((cursor+a,cursor+b,captions[j]))
   graph=graph.rstrip(";")+";[v"+str(len(pictures))+"]format=yuv420p[out]"
   ff(*args,"-filter_complex",graph,
      "-map","[out]","-t",f"{seconds:.3f}",
      "-c:v","libx264","-preset","veryfast","-crf","26","-pix_fmt","yuv420p",scene)
  scenes.append(scene);cursor+=seconds
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
  "duration_seconds":round(total,2),"screen":"full height footage; 172px fixed dark navy header; speech-chunk captions over photo/video",
  "voice":"single Charon narration 1.25x",
  "body_cta_count":0,"final_cta_count":1,
  "actual_voice_transcript_verified":True,"caption_chunks":len(srt),
  "real_clips_count":len(realvideo),"real_photos_count":len(realphotos),
  "sources":cfg["src"],"youtube_uploaded":False
 },ensure_ascii=False,indent=2),encoding="utf-8")
 assert final.stat().st_size>750000
 print("DELIVERABLE_READY",key,final,"BYTES",final.stat().st_size,flush=True)

if __name__=="__main__":
 for n in ["bathroom"]:
  render(n,CONFIG[n])
 print("BATHROOM_CLEANER_SHORT_VERIFIED",flush=True)
