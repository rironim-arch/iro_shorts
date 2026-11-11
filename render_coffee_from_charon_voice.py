"""Assemble a genuinely new narrated coffee-grounds Short from original Gemini WAV scenes.
No old title/cards/narration are reused. Old licensed Pexels footage is cropped to its
unlettered center video portion. The single CTA is drawn ONLY for the final scene.
"""
import json, os, subprocess, sys, wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
import requests

WORK=Path("coffee_three_uses_release")
WORK.mkdir(parents=True,exist_ok=True)
VOICES=Path("voice")
SRC=Path("coffee_grounds_mobile.mp4")
F= imageio_ffmpeg.get_ffmpeg_exe()
W,H=720,1280
SCENE_TIMES=[1.1,6,17,7,2,2,22,26,35,1,0]
BG=(247,241,232,255)
COFFEE=(58,40,31,255)
BRONZE=(158,98,59,255)
STONE=(101,81,68,255)

def ff(*args):
 subprocess.run([F,"-y","-hide_banner","-loglevel","error",*map(str,args)],
                check=True,timeout=180,stdout=subprocess.DEVNULL)

def hangul_font():
 candidates=[
  "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
  "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
  "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"]
 for x in candidates:
  if Path(x).exists():return x
 # Download only OFL-licensed font for internal rendering, never bundle it in output.
 p=WORK/"NanumGothic-Bold.ttf"
 url="https://raw.githubusercontent.com/google/fonts/main/ofl/nanumgothic/NanumGothic-Bold.ttf"
 r=requests.get(url,timeout=40);r.raise_for_status()
 p.write_bytes(r.content)
 assert p.stat().st_size>100000
 return str(p)

FONT_PATH=hangul_font()
def font(n):
 return ImageFont.truetype(FONT_PATH,n)
def lines(d,txt,n,maxw):
 out=[];buf=""
 for word in txt.split():
  candidate=(buf+" "+word).strip()
  if d.textbbox((0,0),candidate,font=font(n))[2] <= maxw:
   buf=candidate
  else:
   if buf:out.append(buf)
   buf=word
 if buf:out.append(buf)
 return out
def card(index,text,ending=False):
 im=Image.new("RGBA",(W,H),BG);d=ImageDraw.Draw(im)
 if ending:
  d.rounded_rectangle((28,47,692,1225),radius=35,fill=(238,223,201,255))
  d.text((360,216),"생활알고리즘",font=font(68),fill=COFFEE,anchor="mm")
  d.text((360,385),"오늘의 생활정보",font=font(36),fill=STONE,anchor="mm")
  d.rounded_rectangle((57,602,663,803),radius=36,fill=COFFEE)
  d.text((360,703),"구독과 좋아요",font=font(64),fill="white",anchor="mm")
  d.text((360,1061),"내일도 유용한 정보로!",font=font(36),fill=BRONZE,anchor="mm")
 else:
  # Entire body artboard is created here from scratch. This is NOT an old MP4 card.
  d.rounded_rectangle((22,34,275,100),radius=25,fill=COFFEE)
  d.text((149,67),"생활알고리즘",font=font(34),fill="white",anchor="mm")
  d.text((690,70),"LIFE GUIDE",font=font(18),fill=BRONZE,anchor="rm")
  d.line((24,122,696,122),fill=(201,179,154),width=3)
  d.text((360,200),"커피 찌꺼기 활용법 3가지",font=font(46),fill=COFFEE,anchor="mm")
  d.rounded_rectangle((25,274,695,765),radius=25,fill=(224,205,177,255))
  # Make only central video window transparent; old footage overlay regions never appear.
  d.rectangle((30,285,690,755),fill=(0,0,0,0))
  d.rounded_rectangle((25,793,695,1160),radius=28,fill=(239,225,206,255))
  d.text((62,846),f"TIP {index+1:02d}",font=font(27),fill=BRONZE,anchor="lm")
  size=41
  txtlines=lines(d,text,size,610)
  if len(txtlines)>3:size=35;txtlines=lines(d,text,size,610)
  if len(txtlines)>4:size=29;txtlines=lines(d,text,size,610)
  top=975-(len(txtlines)-1)*62/2
  for j,line in enumerate(txtlines[:4]):
   d.text((360,top+j*62),line,font=font(size),fill=COFFEE,anchor="mm")
  d.text((360,1214),"생활정보는 짧고 정확하게",font=font(26),fill=STONE,anchor="mm")
 out=WORK/f"overlay_{index:02}.png";im.save(out)
 return out

def wav_duration(p):
 with wave.open(str(p),"rb") as w:return w.getnframes()/w.getframerate()
def srt_stamp(t):
 k=round(t*1000);h,k=divmod(k,3600000);m,k=divmod(k,60000);s,ms=divmod(k,1000)
 return f"{h:02}:{m:02}:{s:02},{ms:03}"

def main():
 assert SRC.is_file(),str(SRC)
 manifest=json.loads((VOICES/"manifest.json").read_text(encoding="utf-8"))["scenes"]
 assert len(manifest)==11
 assert "구독과 좋아요" in manifest[-1]["line"]
 assert all("구독" not in x["line"] and "좋아요" not in x["caption"] and "구독" not in x["caption"] for x in manifest[:-1])
 parts=[];srt=[];offset=0.0
 for i,item in enumerate(manifest):
  raw=VOICES/item["file"];assert raw.is_file(),str(raw)
  speed=WORK/f"voice_{i:02}.wav"
  ff("-i",raw,"-af","atempo=1.25","-ar","24000","-ac","1",speed)
  dur=wav_duration(speed)
  srt.append((offset,offset+dur,item["line"]));offset+=dur
  end=i==len(manifest)-1
  overlay=card(i,item["caption"],ending=end)
  out=WORK/f"scene_{i:02}.mp4"
  if end:
   ff("-f","lavfi","-i","color=c=0xf7f1e8:s=720x1280:r=30",
      "-loop","1","-i",overlay,"-i",speed,
      "-filter_complex","[0:v][1:v]overlay=0:0:shortest=1[v]",
      "-map","[v]","-map","2:a","-t",f"{dur:.3f}",
      "-c:v","libx264","-preset","veryfast","-crf","28",
      "-pix_fmt","yuv420p","-c:a","aac","-b:a","112k",out)
  else:
   t=SCENE_TIMES[i]
   ff("-ss",t,"-i",SRC,"-loop","1","-i",overlay,"-i",speed,
      "-filter_complex","[0:v]crop=720:510:0:340,scale=660:470,pad=720:1280:30:285:color=0xf7f1e8,fps=30[footage];[footage][1:v]overlay=0:0:shortest=1[v]",
      "-map","[v]","-map","2:a","-t",f"{dur:.3f}",
      "-c:v","libx264","-preset","veryfast","-crf","28",
      "-pix_fmt","yuv420p","-c:a","aac","-b:a","112k",out)
  parts.append(out)
  print(f"SCENE {i+1}/11 {dur:.2f}s, END={end}",flush=True)
 concat=WORK/"clips.txt"
 concat.write_text("".join(f"file '{x.name}'\n" for x in parts),encoding="utf-8")
 final=WORK/"coffee_grounds_NEW_3_USES.mp4"
 ff("-safe","0","-f","concat","-i",concat,"-c","copy","-movflags","+faststart",final)
 (WORK/"captions.srt").write_text("\n".join(f"{i+1}\n{srt_stamp(a)} --> {srt_stamp(b)}\n{t}\n" for i,(a,b,t) in enumerate(srt)),encoding="utf-8")
 # QA: All body cards are generated without CTA; scene 11 contains the sole phrase.
 (WORK/"quality_check.json").write_text(json.dumps({
  "duration_seconds":round(offset,2),"scenes":len(parts),
  "cta_narration_count":sum("구독과 좋아요" in x["line"] for x in manifest),
  "cta_body_caption_count":sum("구독" in x["caption"] or "좋아요" in x["caption"] for x in manifest[:-1]),
  "cta_visual_scene_count":1,"version":"new script, old Pexels footage reused without old cards",
  "uploaded_to_youtube":False,
 },ensure_ascii=False,indent=2),encoding="utf-8")
 assert final.stat().st_size>1_000_000
 print("READY",final,"BYTES",final.stat().st_size,"SECONDS",round(offset,2),flush=True)

if __name__=="__main__":main()
