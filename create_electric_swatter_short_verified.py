"""생활알고리즘: electric mosquito racket safety Short.
Actual audio transcribed with Gemini 3.8 Flash, every scene inspected for CTA.
Uses public-domain photographs; no actual electrocution demonstration.
Upload only as a GitHub review MP4, not to YouTube.
"""
import difflib, hashlib, io, json, os, random, re, subprocess, time, wave
from pathlib import Path
from urllib.parse import quote
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
from google import genai
from google.genai import types
import imageio_ffmpeg

ROOT=Path("electric_swatter_review")
ROOT.mkdir(exist_ok=True)
W,H=720,1280
FF=imageio_ffmpeg.get_ffmpeg_exe()
BG="#F7F3EE";INK="#182733";ACC="#E77D3D";MUTED="#66717A";WARN="#BC3F35"
SCENES=[
 ("전기 모기채에 손이 닿으면 어떻게 될까요?","모기채에 손이 닿으면?",0),
 ("전기가 흐르는 금속망에 직접 닿으면 순간적으로 감전될 수 있습니다.","금속망에 닿으면 감전 위험",1),
 ("따끔한 통증이나 깜짝 놀라 손을 움찔하는 반응이 나타날 수 있어요.","순간적인 통증과 놀람",2),
 ("심하면 화상을 입거나 놀라서 다른 곳에 부딪혀 다칠 수도 있습니다.","화상 · 이차 부상 주의",3),
 ("그런데 더 중요한 사실이 있습니다. 전원을 껐다고 바로 안전한 건 아닙니다.","전원 OFF = 즉시 안전? 아닙니다",0),
 ("한국소비자원은 전원을 끈 뒤에도 전류망에 전기가 남을 수 있다고 경고합니다.","전원 꺼도 잔류 전기 주의",1),
 ("따라서 사용 직후에는 절대 금속망을 만지지 마세요.","사용 직후 금속망 접촉 금지",2),
 ("특히 어린이 손이 닿지 않게 보관하고 손상된 제품은 사용하지 마세요.","어린이 접근 금지 · 손상품 사용 금지",3),
 ("가연성 살충제를 뿌린 곳에서는 불이 붙을 수 있어 함께 사용하면 안 됩니다.","가연성 살충제와 함께 사용 금지",0),
 ("호기심에 손으로 직접 시험하지 마세요. 안전이 먼저입니다.","직접 만져서 시험하지 마세요!",1),
 ("구독과 좋아요! 생활알고리즘.","구독과 좋아요",None),
]
PHOTO_FILES=[
 ("Elektronische Fliegenklatsche.jpg","Electric fly swatter upright","Public domain","https://commons.wikimedia.org/wiki/File:Elektronische_Fliegenklatsche.jpg"),
 ("Raketnyamuk.jpg","Electric fly swatter","Public domain","https://commons.wikimedia.org/wiki/File:Raketnyamuk.jpg"),
 ("Электрическая мухобойка.JPG","Electric fly swatter","CC0","https://commons.wikimedia.org/wiki/File:Электрическая_мухобойка.JPG"),
 ("Mosquito destroyer.jpg","Electric fly swatter","Public domain","https://commons.wikimedia.org/wiki/File:Mosquito_destroyer.jpg"),
]
SOURCES=[
 "https://www.kca.go.kr/home/sub.do?menukey=4006&mode=view&no=1002833023&page=3",
 "https://bilder.obi.at/5892967e-12c1-49ea-8da7-b924b7557f4d/document.pdf",
 "https://manuall.co.uk/livarno-ian-364710-electric-fly-swatter/",
]
assert SCENES[-1][0].count("구독과 좋아요")==1
assert all("구독" not in a+b and "좋아요" not in a+b for a,b,_ in SCENES[:-1])

def ff(*args):
 cmd=[FF,"-y","-hide_banner","-loglevel","error",*map(str,args)]
 subprocess.run(cmd,check=True,timeout=120,stdout=subprocess.DEVNULL)

def fpath():
 for p in ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
           "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
           "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"):
  if Path(p).is_file():return p
 p=ROOT/"NanumGothic-Bold.ttf"
 if not p.exists():
  r=requests.get("https://raw.githubusercontent.com/google/fonts/main/ofl/nanumgothic/NanumGothic-Bold.ttf",timeout=25)
  r.raise_for_status();p.write_bytes(r.content)
 return str(p)
FONT=fpath()
def font(s):return ImageFont.truetype(FONT,s)
def wrap(d,t,size,maxw=625):
 words=t.split();out=[];line=""
 for w in words:
  trial=(line+" "+w).strip()
  if d.textbbox((0,0),trial,font=font(size))[2]<=maxw:line=trial
  else:
   if line:out.append(line)
   line=w
 if line:out.append(line)
 return out

def base64photo(filename):
 name=filename.replace(" ","_")
 md5=hashlib.md5(name.encode("utf-8")).hexdigest()
 link=f"https://upload.wikimedia.org/wikipedia/commons/{md5[0]}/{md5[:2]}/{quote(name)}"
 r=requests.get(link,timeout=(10,35),headers={"User-Agent":"LifestyleAlgorithmShorts/1.0 (educational safety video; contact via github.com/rironim-arch/iro_shorts)"})
 r.raise_for_status()
 im=Image.open(io.BytesIO(r.content));im.load()
 if im.width<300 or im.height<300:raise ValueError("undersize image")
 return im.convert("RGB"),link

def fallback_racket():
 im=Image.new("RGB",(1000,950),"#EEE4D7")
 d=ImageDraw.Draw(im)
 d.ellipse((245,95,760,610),fill="#3C5363",outline="#182733",width=22)
 d.ellipse((272,125,733,580),fill="#DDD9D1",outline="#607180",width=12)
 for i in range(300,721,33):
  d.line((i,150,i,552),fill="#8B9392",width=3)
 for j in range(170,560,29):
  d.line((294,j,713,j),fill="#8B9392",width=3)
 d.rounded_rectangle((464,580,548,919),radius=27,fill="#24435E")
 d.rounded_rectangle((478,677,534,727),radius=17,fill=ACC)
 return im

def get_images():
 photos=[];notes=[]
 for filename,desc,license,url in PHOTO_FILES:
  try:
   im,source=base64photo(filename)
   photos.append(im)
   notes.append(f"{desc} | {license} | {url} | {source}")
   print("PUBLIC_DOMAIN_PHOTO",filename,"OK",im.size,flush=True)
  except Exception as e:
   print("PUBLIC_DOMAIN_PHOTO",filename,"UNAVAILABLE",str(e)[:160],flush=True)
 if not photos:
  # Wikimedia servers can rate-limit runners (429); use original, purpose-drawn illustrations.
  base=fallback_racket()
  photos=[base,
    ImageOps.autocontrast(base.crop((165,45,815,720)).resize((1000,950),Image.Resampling.LANCZOS)),
    base.transpose(Image.Transpose.FLIP_LEFT_RIGHT),
    ImageOps.autocontrast(base.crop((325,430,650,930)).resize((1000,950),Image.Resampling.LANCZOS))]
  notes.append("Video visuals: original programmatically drawn safety illustrations; no external stock used.")
  print("ILLUSTRATION_FALLBACK: generated 4 original safety visuals",flush=True)
 (ROOT/"image_credits.txt").write_text("\n".join(notes),encoding="utf-8")
 return photos

def image_crop(img,size=(660,500),focus=0.5):
 iw,ih=img.size;tw,th=size
 scale=max(tw/iw,th/ih)
 new=(max(tw,int(iw*scale)),max(th,int(ih*scale)))
 resized=img.resize(new,Image.Resampling.LANCZOS)
 x=max(0,int((new[0]-tw)*focus))
 y=max(0,(new[1]-th)//2)
 return resized.crop((x,y,x+tw,y+th))
def render_panel(idx,caption,photo,ending=False):
 im=Image.new("RGB",(W,H),BG)
 d=ImageDraw.Draw(im)
 if ending:
  d.rounded_rectangle((28,76,692,1190),radius=42,fill="#F1DFD0")
  d.rounded_rectangle((82,128,638,225),radius=25,fill=INK)
  d.text((360,177),"생활알고리즘",font=font(60),anchor="mm",fill="white")
  d.text((360,385),"전기 모기채 안전 수칙",font=font(43),anchor="mm",fill=INK)
  d.rounded_rectangle((65,586,655,811),radius=38,fill=ACC)
  d.text((360,698),"구독과 좋아요",font=font(64),anchor="mm",fill="white")
  d.text((360,1013),"안전한 생활정보, 매일 하나씩",font=font(33),anchor="mm",fill=MUTED)
 else:
  d.rounded_rectangle((24,26,298,102),radius=26,fill=INK)
  d.text((161,65),"생활알고리즘",font=font(36),anchor="mm",fill="white")
  d.text((692,65),"SAFETY TIP",font=font(21),anchor="rm",fill=ACC)
  d.rounded_rectangle((23,132,697,248),radius=24,fill="#E6DCCF")
  d.text((360,190),"전기 모기채, 손 닿으면?",font=font(50),anchor="mm",fill=INK)
  d.rounded_rectangle((20,270,700,796),radius=32,fill="#DCD8D2")
  frame=image_crop(photo)
  im.paste(frame,(30,282))
  d.rounded_rectangle((20,810,700,1165),radius=33,fill="#F1E8DF")
  d.rounded_rectangle((51,842,210,899),radius=15,fill=ACC)
  d.text((130,871),f"CHECK {idx+1:02}",font=font(25),fill="white",anchor="mm")
  size=46;lines=wrap(d,caption,size)
  if len(lines)>3:size=39;lines=wrap(d,caption,size)
  if len(lines)>3:size=33;lines=wrap(d,caption,size)
  y=998-(len(lines)-1)*60/2
  for k,t in enumerate(lines[:4]):
   d.text((360,y+k*60),t,font=font(size),fill=INK,anchor="mm")
  d.text((360,1220),"확인된 안전수칙 · 직접 감전 실험 금지",font=font(25),fill=MUTED,anchor="mm")
 path=ROOT/f"panel_{idx:02}.png";im.save(path,compress_level=5);return path

client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
def nonmarkup(s):return re.sub(r"[^가-힣0-9A-Za-z]","",s)
def containscta(s):return bool(re.search(r"구\s*독|좋\s*아\s*요",s))
def write_wav(data,mime,p):
 if data.startswith(b"RIFF"):p.write_bytes(data)
 else:
  sr_match=re.search(r"rate=(\d+)",str(mime or ""))
  sr=int(sr_match.group(1)) if sr_match else 24000
  with wave.open(str(p),"wb") as w:
   w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(data)
 with wave.open(str(p),"rb") as w:assert w.getnframes()>10000
def speech(line,dst):
 resp=client.models.generate_content(
  model="gemini-2.5-flash-preview-tts",
  contents=("Read ONLY the following Korean sentence exactly once, without adding, "
   "summarizing or changing ANY words. "
   "Do not add a greeting, transition, outro, or any promotion. "
   "Use natural, clear and confident Korean male speech.\n"
   "<<<SENTENCE>>>\n"+line+"\n<<<END>>>"),
  config=types.GenerateContentConfig(
   response_modalities=["AUDIO"],
   speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))
  ))
 parts=resp.candidates[0].content.parts
 audio=next((p.inline_data for p in parts if p.inline_data and p.inline_data.data),None)
 if not audio:raise RuntimeError("Gemini returned no audio")
 write_wav(audio.data,audio.mime_type,dst)
def asr(path):
 data=path.read_bytes()
 resp=client.models.generate_content(
  model="gemini-3.8-flash",
  contents=["한국어 오디오의 실제 발화를 모두 그대로 받아쓰세요. 오디오 밖의 내용은 추가하지 마세요. 설명 없이 원문 받아쓰기만 출력하세요.",
            types.Part.from_bytes(data=data,mime_type="audio/wav")])
 return (resp.text or "").strip()
def generate_clean(i,line):
 dst=ROOT/f"voice_{i:02}.wav"
 for attempt in range(4):
  try:
   speech(line,dst)
   actual=asr(dst)
   norm=nonmarkup(actual)
   cta=containscta(actual)
   must=(i==len(SCENES)-1)
   goodcta=cta and norm.count("구독")==1 and norm.count("좋아요")==1 if must else not cta
   accuracy=difflib.SequenceMatcher(None,nonmarkup(line),norm).ratio()
   with wave.open(str(dst),"rb") as w:dur=w.getnframes()/w.getframerate()
   print("AUDIO_QA",i+1,"try",attempt+1,"CTA_OK",goodcta,"RATIO",round(accuracy,3),"DURATION",round(dur,1),"HEARD",actual,flush=True)
   if goodcta and accuracy>=0.72 and 0.7<dur<16:return dst,actual
  except Exception as e:
   print("AUDIO_QA_RETRY",i+1,attempt+1,str(e)[:180],flush=True)
  time.sleep(4*(attempt+1))
 raise RuntimeError(f"Scene {i+1} failed exact CTA audio QA: {line}")
def audio_duration(p):
 with wave.open(str(p),"rb") as w:return w.getnframes()/w.getframerate()
def srtstamp(s):
 n=round(s*1000);h,n=divmod(n,3600000);m,n=divmod(n,60000);s,ms=divmod(n,1000)
 return f"{h:02}:{m:02}:{s:02},{ms:03}"

def main():
 photos=get_images()
 verified=[];parts=[];captions=[];offset=0
 for i,(line,caption,idx) in enumerate(SCENES):
  raw,actual=generate_clean(i,line)
  verified.append({"scene":i+1,"expected":line,"actual":actual,"contains_cta":containscta(actual)})
  sped=ROOT/f"narration_{i:02}_125.wav"
  ff("-i",raw,"-af","atempo=1.25","-ar","24000","-ac","1",sped)
  dur=audio_duration(sped)
  captions.append((offset,offset+dur,line));offset+=dur
  png=render_panel(i,caption,photos[(idx or 0)%len(photos)],ending=idx is None)
  scene=ROOT/f"scene_{i:02}.mp4"
  ff("-loop","1","-framerate","30","-i",png,"-i",sped,
     "-t",f"{dur:.3f}","-c:v","libx264","-preset","veryfast","-crf","25",
     "-pix_fmt","yuv420p","-c:a","aac","-b:a","128k",
     "-shortest",scene)
  parts.append(scene)
  print("RENDERED",i+1,"/",len(SCENES),"SECONDS",round(dur,2),flush=True)
 assert sum(x["contains_cta"] for x in verified)==1 and verified[-1]["contains_cta"]
 assert all("구독" not in x[1] and "좋아요" not in x[1] for x in SCENES[:-1])
 listing=ROOT/"concat.txt"
 listing.write_text("".join(f"file '{f.name}'\n" for f in parts),encoding="utf-8")
 final=ROOT/"electric_swatter_hand_contact.mp4"
 ff("-f","concat","-safe","0","-i",listing,"-c","copy","-movflags","+faststart",final)
 (ROOT/"captions.srt").write_text("\n".join(
  f"{i+1}\n{srtstamp(a)} --> {srtstamp(b)}\n{line}\n" for i,(a,b,line) in enumerate(captions)),encoding="utf-8")
 (ROOT/"script.txt").write_text("\n".join(line for line,_,_ in SCENES),encoding="utf-8")
 (ROOT/"sources.txt").write_text("FACT SOURCES\n"+"\n".join(SOURCES)+"\n\nPHOTO CREDIT\n"+
  (ROOT/"image_credits.txt").read_text(encoding="utf-8")+
  "\nPublic-domain and CC0 photographs, if available, are cropped as illustration. Otherwise original drawings are used. No human electrocution performed.\n",encoding="utf-8")
 (ROOT/"qa.json").write_text(json.dumps({
   "duration":round(offset,2),
   "voice":"Gemini Charon, 1.25x",
   "cta_in_body":sum(x["contains_cta"] for x in verified[:-1]),
   "cta_in_ending":int(verified[-1]["contains_cta"]),
   "spoken_cta_count":sum(nonmarkup(x["actual"]).count("구독") for x in verified),
   "visual_cta_ending_only":True,
   "photos_count":len(photos),"scenes":verified,
   "video_type":"Illustrated product safety explainer; public-domain photos only if available; no reenacted electric shock",
   "youtube_uploaded":False
 },ensure_ascii=False,indent=2),encoding="utf-8")
 assert final.stat().st_size>300000
 print("COMPLETE",final,"DURATION",offset,"BYTES",final.stat().st_size,flush=True)
if __name__=="__main__":main()
