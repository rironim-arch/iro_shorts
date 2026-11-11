"""Render a NEW winter moisturizer ingredient Short with actual Charon voice QA.
This intentionally does not use the old Gemini TTS prompt that added 'subscribe & like'
to every scene. Never publish or upload to YouTube: release a review MP4 only.
"""
import json, os, re, subprocess, time, wave, difflib
from pathlib import Path
from google import genai
from google.genai import types
from PIL import Image,ImageDraw,ImageFont
import imageio_ffmpeg
import requests

O=Path("winter_lotion_final")
O.mkdir(exist_ok=True)
FF=imageio_ffmpeg.get_ffmpeg_exe()
W,H=720,1280
TITLE="겨울 바디로션, 이 성분 보세요!"
SCENES=[
 ("겨울마다 피부가 하얗게 일어나고 가렵다면, 바디로션 성분부터 확인하세요.","겨울철 고보습 바디로션 성분부터!",0),
 ("첫째, 글리세린과 히알루론산. 피부가 수분을 유지하도록 돕는 성분입니다.","① 글리세린 · 히알루론산 | 수분 유지",4),
 ("둘째, 세라마이드. 건조해진 피부 장벽을 보완하는 데 도움을 줍니다.","② 세라마이드 | 피부 장벽 보완",2),
 ("셋째, 바셀린과 디메치콘. 피부 표면에서 수분이 빠져나가는 걸 줄여줍니다.","③ 바셀린 · 디메치콘 | 수분 보호",3),
 ("피부가 많이 건조하면 묽은 로션보다 꾸덕한 크림이나 연고형이 더 나을 수 있어요.","심한 건조함에는 크림 · 연고형",0),
 ("제품 성분표에서 글리세린, 세라마이드, 페트롤라툼 같은 이름을 확인해 보세요.","성분표: 글리세린 · 세라마이드 · 페트롤라툼",1),
 ("향료에 민감하다면 무향 제품을 고르고, 처음 쓰는 제품은 작은 부위부터 시험하세요.","민감한 피부 → 무향 · 소량 테스트",5),
 ("샤워 후 물기가 조금 남았을 때 바로 발라주면 수분을 지키는 데 도움이 됩니다.","샤워 직후 촉촉할 때 보습제!",3),
 ("겨울 보습의 핵심은 비싼 브랜드보다 내 피부에 맞는 성분과 제형입니다.","가격보다 중요한 건 성분과 제형",1),
 ("구독과 좋아요! 생활알고리즘.","구독과 좋아요",None),
]
STOCK=[
 (9698782,"woman applying body lotion to arms","https://www.pexels.com/video/a-woman-applying-lotion-on-her-arm-9698782/"),
 (5524950,"scooping cream from jar","https://www.pexels.com/video/a-person-scooping-a-cream-5524950/"),
 (7218428,"woman applying hand cream","https://www.pexels.com/video/a-woman-applying-cream-on-her-hand-7218428/"),
 (9697690,"applying moisturizer to arm","https://www.pexels.com/video/woman-applying-cream-on-her-arm-9697690/"),
 (6006426,"cream applied on hand","https://www.pexels.com/video/woman-applying-a-cream-on-her-hand-6006426/"),
 (7117097,"hand cream at home","https://www.pexels.com/video/video-of-a-woman-applying-hand-lotion-7117097/"),
]
FACT_SOURCES=[
 "https://www.aad.org/public/everyday-care/skin-care-basics/dry/dermatologists-tips-relieve-dry-skin/",
 "https://www.aad.org/public/everyday-care/skin-care-basics/dry/pick-moisturizer",
 "https://www.aad.org/public/everyday-care/skin-care-basics/care/skin-care-tips-hands",
 "https://www.pexels.com/legal-pages/license/"
]
assert len(SCENES)==10
assert all("구독" not in a and "좋아요" not in a and "구독" not in b and "좋아요" not in b for a,b,_ in SCENES[:-1])
assert SCENES[-1][0].count("구독과 좋아요")==1
assert SCENES[-1][1].count("구독과 좋아요")==1

def ff(*args):
 cmd=[FF,"-y","-hide_banner","-loglevel","error",*map(str,args)]
 subprocess.run(cmd,check=True,timeout=150)

def get_font_path():
 for path in ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
              "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
              "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"):
  if Path(path).is_file():return path
 fallback=O/"NanumGothic-Bold.ttf"
 r=requests.get("https://raw.githubusercontent.com/google/fonts/main/ofl/nanumgothic/NanumGothic-Bold.ttf",timeout=35)
 r.raise_for_status();fallback.write_bytes(r.content)
 assert fallback.stat().st_size>100000
 return str(fallback)
FONT=get_font_path()
def font(size):return ImageFont.truetype(FONT,size)

def split(d,t,size,max_w=650):
 out=[];buff=""
 for word in t.split():
  proposal=(buff+" "+word).strip()
  if d.textbbox((0,0),proposal,font=font(size))[2]<=max_w:
   buff=proposal
  else:
   if buff:out.append(buff)
   buff=word
 if buff:out.append(buff)
 return out
def visual_card(idx,caption,ending=False):
 c1=(49,43,66,255); purple=(102,79,119,255); ctext=(65,55,61,255)
 im=Image.new("RGBA",(W,H),(248,245,240,255))
 d=ImageDraw.Draw(im)
 if ending:
  d.rounded_rectangle((35,95,685,1192),radius=44,fill=(235,228,241,255))
  d.text((360,269),"생활알고리즘",font=font(75),fill=c1,anchor="mm")
  d.text((360,417),"겨울 보습, 성분부터!",font=font(41),fill=purple,anchor="mm")
  d.rounded_rectangle((58,610,662,799),radius=31,fill=c1)
  d.text((360,707),"구독과 좋아요",font=font(68),fill="white",anchor="mm")
  d.text((360,1026),"매일 알아두면 좋은 생활정보",font=font(32),fill=ctext,anchor="mm")
 else:
  d.rounded_rectangle((25,37,285,102),radius=21,fill=c1)
  d.text((155,71),"생활알고리즘",font=font(34),fill="white",anchor="mm")
  d.text((691,69),"LIFE GUIDE",font=font(18),fill=purple,anchor="rm")
  d.line((28,126,690,126),fill=(211,195,216),width=3)
  d.text((360,198),TITLE,font=font(45),fill=c1,anchor="mm")
  d.rounded_rectangle((28,276,692,752),radius=27,fill=(223,216,226,255))
  d.rectangle((30,282,690,743),fill=(0,0,0,0))
  d.rounded_rectangle((26,785,694,1156),radius=31,fill=(239,233,242,255))
  d.text((67,837),f"POINT {idx+1:02d}",font=font(28),fill=purple,anchor="lm")
  size=44;rows=split(d,caption,size)
  if len(rows)>3:size=38;rows=split(d,caption,size)
  if len(rows)>4:size=31;rows=split(d,caption,size)
  top=971-(len(rows)-1)*64/2
  for j,line in enumerate(rows[:4]):
   d.text((360,top+64*j),line,font=font(size),fill=c1,anchor="mm")
  d.text((360,1202),"실생활에 바로 쓰는 생활정보",font=font(26),fill=purple,anchor="mm")
 p=O/f"overlay_{idx:02}.png";im.save(p)
 return p

S=requests.Session();S.headers.update({"User-Agent":"Mozilla/5.0 (X11; Linux x86_64)"})
def probe(path):
 r=subprocess.run([FF,"-v","error","-i",str(path),"-f","null","-"],capture_output=True,timeout=20)
 return r.returncode==0

def stock_download(item):
 id,_,_=item
 p=O/f"pexels_{id}.mp4"
 urls=[f"https://www.pexels.com/video/download/{id}/"]
 for fps in (25,30,24,60):
  for dim in ("1080_1920","1920_1080","720_1280","1280_720","540_960","960_540"):
   urls.append(f"https://videos.pexels.com/video-files/{id}/{id}-hd_{dim}_{fps}fps.mp4")
 for j,u in enumerate(urls):
  try:
   if j:
    h=S.head(u,timeout=3)
    if h.status_code!=200 or "video" not in h.headers.get("content-type","").lower():continue
   with S.get(u,stream=True,timeout=(6,50)) as r:
    r.raise_for_status()
    typ=r.headers.get("content-type","").lower()
    if not any(k in typ for k in ("video","mp4","octet-stream")):continue
    with p.open("wb") as f:
     total=0
     for chunk in r.iter_content(1024*1024):
      if not chunk:continue
      total+=len(chunk)
      if total>85_000_000:raise ValueError("stock clip exceeds size cap")
      f.write(chunk)
   if p.stat().st_size>100000 and probe(p):return p
  except Exception:pass
  p.unlink(missing_ok=True)
 return None

CLIENT=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
def normalize(t):return re.sub(r"[^0-9A-Za-z가-힣]","",t)
def has_cta(t):return bool(re.search(r"구\s*독|좋\s*아\s*요",t))
def wav_write(raw,mime,p):
 if raw.startswith(b"RIFF"):p.write_bytes(raw)
 else:
  m=re.search(r"rate=(\d+)",(mime or "").lower())
  with wave.open(str(p),"wb") as wf:
   wf.setnchannels(1);wf.setsampwidth(2);wf.setframerate(int(m.group(1)) if m else 24000)
   wf.writeframes(raw)
 with wave.open(str(p),"rb") as wf:assert wf.getnframes()>10000
def asr(wav):
 request=["이 한국어 오디오에 실제로 들리는 말을 모두 정확히 받아쓰세요. "
          "실제 발화에 없는 문구를 추가하지 마세요. 다른 설명 없이 받아쓰기만 적으세요.",
          types.Part.from_bytes(data=wav.read_bytes(),mime_type="audio/wav")]
 result=CLIENT.models.generate_content(model="gemini-3.8-flash",contents=request)
 return (result.text or "").strip()
def voice_line(idx,line):
 dest=O/f"charon_{idx:02}.wav"
 for attempt in range(4):
  try:
   prompt=("Read exactly the Korean text between delimiters, once. "
      "No introductions, no promotions, no extra words. "
      "Calm clear natural Korean male voice.\n"
      "<<<BEGIN>>>\n"+line+"\n<<<END>>>")
   result=CLIENT.models.generate_content(
    model="gemini-2.5-flash-preview-tts",contents=prompt,
    config=types.GenerateContentConfig(
     response_modalities=["AUDIO"],
     speech_config=types.SpeechConfig(
      voice_config=types.VoiceConfig(
       prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
   data=next((part.inline_data for part in result.candidates[0].content.parts
              if part.inline_data and part.inline_data.data),None)
   if not data:raise RuntimeError("No speech audio returned")
   wav_write(data.data,data.mime_type,dest)
   transcript=asr(dest)
   cta_ok=has_cta(transcript) if idx==len(SCENES)-1 else not has_cta(transcript)
   accuracy=difflib.SequenceMatcher(None,normalize(line),normalize(transcript)).ratio()
   print("VOICE",idx+1,"attempt",attempt+1,"CTA_OK",cta_ok,"ACCURACY",round(accuracy,3),
         "ACTUALLY_SPOKEN",transcript,flush=True)
   if cta_ok and accuracy>=0.72:return dest,transcript
  except Exception as e:
   print("VOICE_RETRY",idx+1,attempt+1,str(e)[:220],flush=True)
  time.sleep((attempt+1)*4)
 raise RuntimeError(f"VOICE QA FAILED scene {idx+1} - refusing release")

def wav_seconds(p):
 with wave.open(str(p),"rb") as w:return w.getnframes()/w.getframerate()
def stamp(t):
 n=round(t*1000);h,n=divmod(n,3600000);m,n=divmod(n,60000);s,ms=divmod(n,1000)
 return f"{h:02}:{m:02}:{s:02},{ms:03}"

def main():
 # Acquire a handful of licensed real clips; skip unavailable stock rather than fake footage.
 clips={}
 for item in STOCK:
  clip=stock_download(item)
  if clip:clips[STOCK.index(item)]=clip
  print("STOCK",item[0],"OK" if clip else "UNAVAILABLE",flush=True)
 if len(clips)<2:raise RuntimeError("Less than 2 authentic licensed stock clips; render aborted")

 voice=[];qa=[]
 for idx,(line,caption,stock_idx) in enumerate(SCENES):
  wav,recognized=voice_line(idx,line)
  voice.append(wav)
  qa.append({"scene":idx+1,"expected":line,"spoken":recognized,"cta":has_cta(recognized)})
 assert sum(x["cta"] for x in qa)==1 and qa[-1]["cta"]
 # Render each scene using only the just-audited WAV, never reuse older audio.
 pieces=[];timing=[];start=0.0
 for idx,((line,caption,preferred),raw) in enumerate(zip(SCENES,voice)):
  clean=O/f"speed_{idx:02}.wav"
  ff("-i",raw,"-af","atempo=1.25","-ar","24000","-ac","1",clean)
  dur=wav_seconds(clean)
  timing.append((start,start+dur,line));start+=dur
  png=visual_card(idx,caption,ending=preferred is None)
  part=O/f"scene_{idx:02}.mp4"
  if preferred is None:
   ff("-f","lavfi","-i","color=c=0xf8f5f0:s=720x1280:r=30",
      "-loop","1","-i",png,"-i",clean,
      "-filter_complex","[0:v][1:v]overlay=0:0:shortest=1[v]",
      "-map","[v]","-map","2:a:0","-t",f"{dur:.3f}",
      "-c:v","libx264","-preset","veryfast","-crf","27","-pix_fmt","yuv420p",
      "-c:a","aac","-b:a","112k",part)
  else:
   src=clips.get(preferred)
   if src is None:src=list(clips.values())[idx%len(clips)]
   ff("-stream_loop","-1","-i",src,"-loop","1","-i",png,"-i",clean,
      "-filter_complex",
      "[0:v]scale=660:462:force_original_aspect_ratio=increase,crop=660:462,"
      "pad=720:1280:30:282:color=0xf8f5f0,fps=30[footage];"
      "[footage][1:v]overlay=0:0:shortest=1[v]",
      "-map","[v]","-map","2:a:0","-t",f"{dur:.3f}",
      "-c:v","libx264","-preset","veryfast","-crf","27","-pix_fmt","yuv420p",
      "-c:a","aac","-b:a","112k",part)
  pieces.append(part)
  print("SCENE_RENDERED",idx+1,"SECONDS",round(dur,2),flush=True)
 indexfile=O/"concat.txt"
 indexfile.write_text("".join(f"file '{p.name}'\n" for p in pieces),encoding="utf-8")
 result=O/"winter_body_lotion_verified.mp4"
 ff("-safe","0","-f","concat","-i",indexfile,"-c","copy","-movflags","+faststart",result)
 (O/"captions.srt").write_text("\n".join(
  f"{j+1}\n{stamp(a)} --> {stamp(b)}\n{line}\n" for j,(a,b,line) in enumerate(timing)),encoding="utf-8")
 (O/"script.txt").write_text("\n".join(line for line,caption,_ in SCENES),encoding="utf-8")
 (O/"qa.json").write_text(json.dumps({
  "duration_seconds":round(start,2),
  "voice":"Gemini 2.5 Flash TTS Charon","speed":1.25,
  "body_cta_count":sum(x["cta"] for x in qa[:-1]),
  "final_cta_count":int(qa[-1]["cta"]),
  "verified_by":"Gemini 3.8 Flash ASR of actual scene WAV",
  "scenes":qa,"download_safety":"review only; not published to YouTube",
  "stock_clips":{str(STOCK[i][0]):STOCK[i][2] for i in clips},
 },ensure_ascii=False,indent=2),encoding="utf-8")
 (O/"sources.txt").write_text("\n".join(FACT_SOURCES+[""]+[x[2] for x in STOCK]),encoding="utf-8")
 assert result.stat().st_size>500_000
 print("READY",result,"SECONDS",round(start,2),"BYTES",result.stat().st_size,flush=True)
if __name__=="__main__":main()
