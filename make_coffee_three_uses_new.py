"""LifestyleAlgorithm: NEW coffee-ground 3-use Shorts; not an edit of an older MP4.
Every shot and text panel is generated from scratch.
The phrase 구독과 좋아요 is allowed only in the FINAL scene.
"""
import asyncio, json, re, subprocess
from pathlib import Path
import requests
from PIL import Image,ImageDraw,ImageFont
from gemini_charon_tts import speech

ROOT=Path("out_coffee_three_uses")
ROOT.mkdir(exist_ok=True)
W,H=720,1280
STOCK=[
    (6201662,"coffee grounds into espresso portafilter","https://www.pexels.com/video/coffee-grounds-falling-to-the-portafilter-6201662/"),
    (5540801,"drip coffee brewing","https://www.pexels.com/video/hot-water-getting-poured-on-ground-coffee-5540801/"),
    (5418706,"refrigerator interior","https://www.pexels.com/video/a-woman-getting-food-from-a-refrigerator-5418706/"),
    (37322214,"hand painting paper (illustration of dyeing, not actual coffee dye)","https://www.pexels.com/video/close-up-of-hand-painting-with-brush-37322214/"),
    (6203894,"paintbrush on paper (illustration only)","https://www.pexels.com/video/a-person-painting-on-the-table-6203894/"),
    (6160039,"compost handling","https://www.pexels.com/video/organic-stuff-being-taken-from-basket-6160039/"),
    (5910449,"sorting compost","https://www.pexels.com/video/sorting-out-compost-for-gardening-5910449/"),
]
# The 3-tuple is (spoken narration, short bottom description, preferred stock scene).
SCENES=[
 ("커피 찌꺼기, 그냥 버리시나요? 활용법은 뭐가 있을까요?","커피 찌꺼기의 놀라운 3가지 활용법",0),
 ("첫 번째, 냄새 관리입니다. 사용한 찌꺼기는 충분히 말려 작은 그릇에 담아두세요.","첫 번째  |  충분히 말려 탈취 보조",0),
 ("냉장고나 신발장에 두면 냄새 관리에 보조적으로 활용할 수 있어요.","냉장고·신발장 냄새 관리에 활용",2),
 ("단, 젖은 찌꺼기는 곰팡이가 생기기 쉬우니 반드시 바싹 말리세요.","습기 주의!  젖은 채 보관하지 않기",1),
 ("두 번째, 천연 염색입니다. 찌꺼기를 따뜻한 물에 우린 다음 걸러보세요.","두 번째  |  따뜻한 물에 우려 거르기",0),
 ("커피색 물로 종이에 빈티지한 갈색을 낼 수 있어요. 먼저 작은 종이에 시험해 보세요.","종이 염색 · 빈티지 갈색 만들기",3),
 ("세 번째, 퇴비 재료로 활용해 보세요. 낙엽 같은 다른 재료와 함께 섞는 방법입니다.","세 번째  |  낙엽과 섞어 퇴비로",5),
 ("커피 찌꺼기는 퇴비 전체 부피의 이십 퍼센트 이하로 넣는 것이 좋습니다.","퇴비의 20% 이하만 사용",6),
 ("화분에 두껍게 뿌리거나 싱크대 배수구에 버리는 건 피하세요.","주의!  화분에 두껍게 · 배수구 투입 금지",5),
 ("말리고, 물들이고, 퇴비에 섞고! 오늘부터 커피 찌꺼기를 더 똑똑하게 활용하세요.","핵심: 충분히 말리고, 적당히 활용!",0),
 ("구독과 좋아요! 생활알고리즘.","구독과 좋아요",None),
]
SOURCES=[
 "https://www.regrounds.org/guide",
 "https://groundsforrecycling.co.uk/at-home-toolkit/a-guide-to-making-art-with-used-coffee-grounds/",
 "https://pubs.extension.wsu.edu/product/using-coffee-grounds-in-gardens-and-landscapes-home-garden-series/",
 "https://www.pexels.com/legal-pages/license/",
]
assert sum("구독과 좋아요" in t for t,c,v in SCENES)==1
assert all("구독" not in a and "좋아요" not in b for a,b,_ in SCENES[:-1])
S=requests.Session()
S.headers.update({"User-Agent":"Mozilla/5.0"})

def run(*args):
 subprocess.run(args,check=True,stdout=subprocess.DEVNULL)
def probe(path):
 p=subprocess.run(["ffprobe","-v","error","-select_streams","v:0",
  "-show_entries","stream=width,height","-of","json",str(path)],capture_output=True,text=True)
 try:
  d=json.loads(p.stdout)
  return bool(d.get("streams") and d["streams"][0].get("width"))
 except: return False
def fetch(id):
 out=ROOT/f"pexels_{id}.mp4"
 if out.exists() and probe(out):return out
 urls=[f"https://www.pexels.com/video/download/{id}/"]
 for fps in (25,30,24,50,60):
  for dim in ("1080_1920","1920_1080","720_1280","1280_720","540_960","960_540"):
   urls.append(f"https://videos.pexels.com/video-files/{id}/{id}-hd_{dim}_{fps}fps.mp4")
 for j,u in enumerate(urls):
  try:
   if j:
    h=S.head(u,timeout=3)
    if h.status_code!=200 or "video" not in h.headers.get("content-type",""):continue
   with S.get(u,stream=True,timeout=(6,45)) as r:
    r.raise_for_status()
    typ=r.headers.get("content-type","").lower()
    if not any(x in typ for x in ("video","mp4","octet-stream")):continue
    with out.open("wb") as f:
     n=0
     for b in r.iter_content(1024*1024):
      if b:
       n+=len(b)
       if n>100000000:raise RuntimeError("stock size limit")
       f.write(b)
   if probe(out):return out
  except Exception:pass
  out.unlink(missing_ok=True)
 return None

FP="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FR="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
def font(n,bold=True):return ImageFont.truetype(FP if bold else FR,n)
def split_lines(d,s,ft,max_width=640):
 if "\n" in s:
  return [x for x in s.split("\n") if x]
 words=s.split()
 out=[];line=""
 for x in words:
  trial=(line+" "+x).strip()
  if d.textbbox((0,0),trial,font=ft)[2]<=max_width:
   line=trial
  else:
   if line:out.append(line)
   line=x
 if line:out.append(line)
 return out

def panel(i,caption,ending=False):
 im=Image.new("RGBA",(W,H),(248,242,231,255))
 d=ImageDraw.Draw(im)
 brown=(64,42,34,255);soft=(123,83,55,255);muted=(123,111,98,255)
 if ending:
  d.rounded_rectangle((36,55,684,1225),radius=46,fill=(237,223,201,255))
  d.text((360,230),"생활알고리즘",font=font(70),anchor="mm",fill=brown)
  d.text((360,412),"오늘의 생활정보",font=font(42),anchor="mm",fill=soft)
  d.rounded_rectangle((65,615,655,820),radius=45,fill=brown)
  d.text((360,719),"구독과 좋아요",font=font(64),anchor="mm",fill=(255,255,255,255))
  d.text((360,1000),"유용했다면 저장해두세요",font=font(35,False),anchor="mm",fill=soft)
 else:
  d.rounded_rectangle((26,35,269,99),radius=22,fill=brown)
  d.text((146,68),"생활알고리즘",font=font(34),anchor="mm",fill=(255,255,255,255))
  d.text((685,64),"LIFE GUIDE",font=font(18),anchor="rm",fill=soft)
  d.line((30,121,690,121),fill=(199,178,155,255),width=3)
  d.text((360,193),"커피 찌꺼기 활용법 3가지",font=font(47),anchor="mm",fill=brown)
  d.rounded_rectangle((30,265,690,760),radius=30,fill=(228,210,186,255))
  # Let the real B-roll show in a compact window. Never add any CTA on body scenes.
  d.rectangle((36,275,684,750),fill=(0,0,0,0))
  d.rounded_rectangle((28,790,692,1160),radius=32,fill=(236,224,207,255))
  d.text((66,842),f"{i+1:02d} / {len(SCENES)-1:02d}",font=font(25),anchor="lm",fill=soft)
  lines=split_lines(d,caption,font(42),620)
  if len(lines)>3:lines=split_lines(d,caption,font(34),620)
  size=42 if len(lines)<=3 else 34
  if len(lines)>3:lines=lines[:4]
  top=960-(len(lines)-1)*58/2
  for n,line in enumerate(lines):
   d.text((360,top+n*58),line,font=font(size),anchor="mm",fill=brown)
  d.text((360,1216),"알아두면 쓸모 있는 생활정보",font=font(26,False),anchor="mm",fill=muted)
 out=ROOT/f"overlay_{i:02}.png";im.save(out)
 return out

def duration(p):
 return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration",
  "-of","default=nokey=1:noprint_wrappers=1",str(p)],text=True))
def tcode(s):
 n=round(s*1000);h,n=divmod(n,3600000);m,n=divmod(n,60000);sec,ms=divmod(n,1000)
 return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"

async def main():
 usable={}
 for i,desc,url in STOCK:
  p=await asyncio.to_thread(fetch,i)
  if p:usable[i]=p
  print("BROLL",i, "OK" if p else "SKIP",flush=True)
 if not usable:raise RuntimeError("No licensed stock footage could be downloaded.")
 segments=[];subtitles=[];at=0
 for i,(voice,caption,pref) in enumerate(SCENES):
  raw=ROOT/f"narration_{i:02}.wav"
  await speech(voice,raw)
  audio=ROOT/f"voice_speed_{i:02}.wav"
  run("ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(raw),"-af","atempo=1.25",
      "-ar","24000","-ac","1",str(audio))
  d=duration(audio)
  subtitles.append((at,at+d,voice));at+=d
  ending=pref is None
  visual=ROOT/f"visual_{i:02}.mp4"
  if ending:
   run("ffmpeg","-y","-loglevel","error","-f","lavfi","-i",
       "color=c=0xf8f2e7:s=720x1280:r=30","-t",f"{d:.3f}",
       "-c:v","libx264","-preset","veryfast","-pix_fmt","yuv420p",str(visual))
  else:
   chosen=usable.get(STOCK[pref][0])
   if not chosen:chosen=list(usable.values())[i%len(usable)]
   run("ffmpeg","-y","-loglevel","error","-stream_loop","-1","-i",str(chosen),
      "-t",f"{d:.3f}","-vf",
      "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,fps=30",
      "-an","-c:v","libx264","-preset","veryfast","-crf","28","-pix_fmt","yuv420p",str(visual))
  over=panel(i,caption,ending)
  part=ROOT/f"scene_{i:02}.mp4"
  run("ffmpeg","-y","-loglevel","error","-i",str(visual),"-loop","1","-i",str(over),"-i",str(audio),
    "-filter_complex","[0:v][1:v]overlay=0:0:shortest=1[v]",
    "-map","[v]","-map","2:a","-t",f"{d:.3f}",
    "-c:v","libx264","-preset","veryfast","-crf","25",
    "-pix_fmt","yuv420p","-c:a","aac","-b:a","112k",str(part))
  segments.append(part)
  print("SCENE",i+1,"SECONDS",round(d,2),flush=True)
 listing=ROOT/"segments.txt"
 listing.write_text("".join(f"file '{p.name}'\n" for p in segments),encoding="utf-8")
 out=ROOT/"coffee_three_uses_FINAL.mp4"
 run("ffmpeg","-y","-loglevel","error","-safe","0","-f","concat",
  "-i",str(listing),"-c","copy","-movflags","+faststart",str(out))
 (ROOT/"captions.srt").write_text("\n".join(
  f"{i+1}\n{tcode(a)} --> {tcode(b)}\n{text}\n" for i,(a,b,text) in enumerate(subtitles)),encoding="utf-8")
 (ROOT/"script.txt").write_text("\n".join(t for t,_,_ in SCENES),encoding="utf-8")
 (ROOT/"sources.txt").write_text("\n".join(SOURCES+[""]+[
  f"Pexels {id}: {desc}, {url}; used: {id in usable}" for id,desc,url in STOCK]),encoding="utf-8")
 (ROOT/"metadata.json").write_text(json.dumps({
   "title":"커피 찌꺼기 그냥 버리시나요? 의외의 활용법 3가지! | 생활알고리즘 #shorts",
   "duration_seconds":duration(out),"resolution":"720x1280",
   "voice":"Gemini Charon 1.25x","cta_count_narration":1,
   "cta_body_count":0,"cta_final_scene_only":True,
   "broll_clips_used":list(usable),"youtube_uploaded":False,
   "description":"커피 찌꺼기를 그냥 버리셨나요? 건조 후 냄새 관리, 종이 염색, 퇴비 활용까지! #생활알고리즘 #커피찌꺼기 #생활정보 #shorts"
 },ensure_ascii=False,indent=2),encoding="utf-8")
 print("FINISHED",out,"SECONDS",duration(out),flush=True)

if __name__=="__main__":
 asyncio.run(main())
