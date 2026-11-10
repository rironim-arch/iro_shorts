"""Produce a review-only 1080x1920 tumbler Short with real Pexels B-roll and Gemini Charon.
No YouTube upload; source and footage license metadata are recorded in the artifact.
"""
import asyncio
import json
import os
import re
import subprocess
import wave
from pathlib import Path
from urllib.parse import unquote
import requests
from PIL import Image, ImageDraw, ImageFont
from gemini_charon_tts import speech

ROOT = Path("out_tumbler_short")
ROOT.mkdir(parents=True, exist_ok=True)
W,H = 1080,1920
RATE = 1.25
STOCK = [
    (8676998, "물병에 물 붓는 세로 실사", "https://www.pexels.com/video/a-person-pouring-water-in-the-bottle-8676998/"),
    (5564279, "스테인리스 용기에 물 붓는 실사", "https://www.pexels.com/video/pouring-hot-water-in-a-container-5564279/"),
    (8287067, "물병을 흐르는 물에 세척하는 실사", "https://www.pexels.com/video/a-person-washing-a-glass-bottle-in-a-sink-8287067/"),
    (12475201, "보온병에서 금속컵에 물 따르는 실사", "https://www.pexels.com/video/pouring-water-into-metal-cup-12475201/"),
    (4109221, "세척 장면과 손 동작 실사", "https://www.pexels.com/video/house-apartment-home-clean-4109221/"),
]
SCENES = [
    ("텀블러, 몇 년째 쓰고 계신가요?", "텀블러\n언제 바꿔야 할까?",0),
    ("스테인리스 텀블러는 일 년마다 무조건 바꿀 필요는 없습니다.", "무조건 1년 교체?\n아닙니다",1),
    ("중요한 건 사용한 기간이 아니라, 지금 상태입니다.", "연식보다 중요한 건\n제품 상태",0),
    ("내부에 심한 부식이나 코팅 손상이 있다면, 사용을 멈추고 제조사에 확인하세요.", "첫째\n내부 부식 · 코팅 손상",1),
    ("뚜껑 패킹에 지워지지 않는 곰팡이나 균열이 있다면, 먼저 패킹을 교체하세요.", "둘째\n패킹 곰팡이 · 균열",2),
    ("보온이나 보냉 성능이 갑자기 떨어졌다면, 진공 단열 손상을 의심할 수 있어요.", "셋째\n보온 · 보냉 성능 저하",3),
    ("본체가 심하게 찌그러졌거나, 부품을 점검해도 계속 샌다면 교체를 고려하세요.", "넷째\n찌그러짐 · 지속 누수",1),
    ("단순한 커피 얼룩이나 냄새는 먼저 제품 설명서대로 세척해 보세요.", "얼룩만으로\n바로 버리지 마세요",4),
    ("세척 가능한 패킹은 분리해 씻고, 뚜껑과 몸체를 충분히 말리세요.", "패킹 분리 세척\n완전 건조",2),
    ("텀블러는 몇 년 썼느냐보다 얼마나 안전하게 관리했느냐가 중요합니다.", "교체 주기보다\n관리 상태",0),
    ("도움이 됐다면 구독과 좋아요! 생활알고리즘.", "구독 · 좋아요\n생활알고리즘",None),
]
SOURCES = [
    "https://www.zojirushi.com/app/faq/vacuum-insulated-mugs-bottles",
    "https://www.stanley1913.com/pages/faq/help",
    "https://www.pexels.com/legal-pages/license/",
]
HEADERS={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/123.0 Safari/537.36"}
SESSION=requests.Session()
SESSION.headers.update(HEADERS)

def cmd(*args):
    subprocess.run(args,check=True,stdout=subprocess.DEVNULL)

def probe(path):
    try:
        r=subprocess.run(["ffprobe","-v","error","-select_streams","v:0",
          "-show_entries","stream=codec_name,width,height","-of","json",str(path)],
          capture_output=True,text=True,timeout=20)
        v=json.loads(r.stdout or "{}").get("streams",[])
        return bool(v and v[0].get("width",0)>100)
    except Exception: return False

def download_clip(id):
    output=ROOT/f"pexels_{id}.mp4"
    if output.exists() and probe(output): return output
    candidates=[f"https://www.pexels.com/video/download/{id}/"]
    # The Pexels download endpoint typically redirects to the original MP4.
    # If redirected downloads are unavailable, try video CDN renditions.
    for fps in (25,24,30,50,60):
        for dim in ("1080_1920","1920_1080","720_1280","1280_720","540_960","960_540","2160_3840","3840_2160"):
            candidates.append(f"https://videos.pexels.com/video-files/{id}/{id}-hd_{dim}_{fps}fps.mp4")
    # Try current public endpoint first, avoid broad scraping of Pexels.
    for u in candidates:
        try:
            if len(candidates)>1 and u!=candidates[0]:
                h=SESSION.head(u,timeout=5,allow_redirects=True)
                if h.status_code!=200 or "video" not in h.headers.get("content-type","").lower(): continue
            with SESSION.get(u,stream=True,timeout=(8,70),allow_redirects=True) as r:
                r.raise_for_status()
                typ=r.headers.get("content-type","").lower()
                if not any(t in typ for t in ("video","octet-stream","mp4")): continue
                with open(output,"wb") as f:
                    total=0
                    for block in r.iter_content(512*1024):
                        if not block:continue
                        total+=len(block)
                        if total>130_000_000:raise ValueError("stock clip over size cap")
                        f.write(block)
            if probe(output):return output
        except Exception:
            pass
        output.unlink(missing_ok=True)
    return None

def font(size,bold=True):
    p="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    return ImageFont.truetype(p,size)

def wrap_text(draw,text,size=82,limit=900):
    lines=[]
    for line in text.split("\n"):
        buffer=""
        for word in line.split():
            trial=f"{buffer} {word}".strip()
            if draw.textbbox((0,0),trial,font=font(size))[2] <= limit:
                buffer=trial
            else:
                if buffer:lines.append(buffer)
                buffer=word
        if buffer:lines.append(buffer)
    return lines

def overlay(index,subtitle,closing=False):
    img=Image.new("RGBA",(W,H),(0,0,0,0))
    d=ImageDraw.Draw(img)
    if closing:
        d.rectangle((0,0,W,H),fill=(14,35,38,255))
        d.rounded_rectangle((100,520,980,1390),radius=56,fill=(250,248,239,255))
        d.text((540,650),"생활알고리즘",font=font(85),fill=(28,56,61),anchor="mm")
        d.text((540,950),"구독과 좋아요",font=font(84),fill=(20,65,65),anchor="mm")
        d.text((540,1190),"매일 쓸모 있는 생활정보",font=font(48),fill=(40,58,60),anchor="mm")
    else:
        d.rounded_rectangle((42,85,550,195),radius=30,fill=(19,40,44,235))
        d.text((296,142),"생활알고리즘",font=font(61),fill=(255,255,255),anchor="mm")
        d.rounded_rectangle((42,260,1038,470),radius=39,fill=(18,35,40,214))
        d.text((540,365),"텀블러 교체 신호 4가지",font=font(70),fill=(252,252,250),anchor="mm")
        d.rounded_rectangle((35,1290,1045,1690),radius=44,fill=(13,28,33,236))
        lines=wrap_text(d,subtitle,83,910)
        if len(lines)>3:
            lines=wrap_text(d,subtitle,72,920)
        step=110
        top=1490-(len(lines)-1)*step/2
        for j,line in enumerate(lines):
            d.text((540,top+j*step),line,font=font(83 if len(lines)<=3 else 72),fill=(253,249,236),anchor="mm",stroke_width=0)
        d.rounded_rectangle((65,1790,1010,1810),radius=9,fill=(235,235,230,90))
        d.rounded_rectangle((65,1790,65+int(945*(index+1)/len(SCENES)),1810),radius=9,fill=(250,187,87,255))
    path=ROOT/f"overlay_{index:02}.png"
    img.save(path)
    return path

def seconds(path):
    return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration",
       "-of","default=nokey=1:noprint_wrappers=1",str(path)],text=True).strip())

def stamp(t):
    n=round(t*1000)
    h,n=divmod(n,3600000);m,n=divmod(n,60000);s,ms=divmod(n,1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

async def main():
    usable={}
    for id,_,url in STOCK:
        p=await asyncio.to_thread(download_clip,id)
        if p:usable[id]=p
        print("STOCK",id, "ok" if p else "unavailable",flush=True)
    if not usable:
        raise RuntimeError("No licensed Pexels video clips downloadable. Refusing to claim real-footage production.")
    # Require actual footage for all narration scenes; only closing card is graphic.
    segments=[]; timings=[]; cursor=0
    for index,(line,caption,preferred) in enumerate(SCENES):
        raw=ROOT/f"take_{index:02}.wav"
        await speech(line,raw)
        sped=ROOT/f"speed_{index:02}.wav"
        cmd("ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(raw),"-af","atempo=1.25",
            "-ac","1","-ar","24000",str(sped))
        dur=seconds(sped)
        timings.append((cursor,cursor+dur,line))
        cursor+=dur
        background=ROOT/f"base_{index:02}.mp4"
        closing=preferred is None
        if closing:
            cmd("ffmpeg","-y","-hide_banner","-loglevel","error","-f","lavfi","-i",
                "color=c=0x12272a:s=1080x1920:r=30","-t",f"{dur:.4f}",
                "-c:v","libx264","-preset","veryfast","-pix_fmt","yuv420p",str(background))
        else:
            stock_id=STOCK[preferred][0]
            src=usable.get(stock_id)
            if src is None:
                src=list(usable.values())[index%len(usable)]
            cmd("ffmpeg","-y","-hide_banner","-loglevel","error","-stream_loop","-1",
                "-i",str(src),"-t",f"{dur:.4f}","-vf",
                "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30",
                "-an","-c:v","libx264","-preset","veryfast","-crf","26","-pix_fmt","yuv420p",str(background))
        graphic=overlay(index,caption,closing)
        rendered=ROOT/f"scene_{index:02}.mp4"
        cmd("ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(background),"-loop","1",
            "-i",str(graphic),"-i",str(sped),"-filter_complex","[0:v][1:v]overlay=0:0:shortest=1[v]",
            "-map","[v]","-map","2:a:0","-c:v","libx264","-preset","veryfast",
            "-crf","23","-pix_fmt","yuv420p","-c:a","aac","-b:a","128k","-t",f"{dur:.4f}",str(rendered))
        segments.append(rendered)
        print("SCENE",index+1,"seconds",round(dur,2),flush=True)
    concat=ROOT/"concat.txt"
    concat.write_text("".join("file '"+p.name+"'\n" for p in segments),encoding="utf-8")
    output=ROOT/"tumbler_review_short.mp4"
    cmd("ffmpeg","-y","-hide_banner","-loglevel","error","-safe","0","-f","concat","-i",str(concat),
        "-c","copy","-movflags","+faststart",str(output))
    (ROOT/"captions.srt").write_text("\n".join(f"{i+1}\n{stamp(a)} --> {stamp(b)}\n{txt}\n"
      for i,(a,b,txt) in enumerate(timings)),encoding="utf-8")
    (ROOT/"script.txt").write_text("\n".join(line for line,_,_ in SCENES),encoding="utf-8")
    (ROOT/"sources_and_rights.txt").write_text("OFFICIAL FACT SOURCES\n"+"\n".join(SOURCES)+
       "\n\nPEXELS STOCK VIDEO CLIPS (Pexels License)\n"+
       "\n".join(f"{id} {label}: {url}; downloaded={id in usable}" for id,label,url in STOCK)+
       "\nhttps://www.pexels.com/legal-pages/license/\n"+
       "\nHuman review required: footage context, specific tumbler manual, sound and captions.\n",encoding="utf-8")
    (ROOT/"metadata.json").write_text(json.dumps({
        "title":"텀블러, 몇 년 쓰면 바꿔야 할까? | 교체 신호 4가지 #shorts",
        "voice":"Gemini 2.5 Flash TTS Charon","speed":RATE,
        "duration_seconds":cursor,"resolution":"1080x1920",
        "real_footage_scene_count":len(SCENES)-1,
        "total_scenes":len(SCENES),
        "status":"DRAFT_REVIEW_REQUIRED",
        "youtube_uploaded":False,
        "usable_stock_ids":list(usable.keys()),
        "description":"텀블러 교체 시기는 연수가 아니라 상태가 중요합니다. 패킹·내부 손상·단열·누수 점검법. #생활알고리즘 #텀블러 #생활상식 #shorts"
        },ensure_ascii=False,indent=2),encoding="utf-8")
    print("READY",output,"duration",cursor,flush=True)

if __name__=="__main__":
    asyncio.run(main())
