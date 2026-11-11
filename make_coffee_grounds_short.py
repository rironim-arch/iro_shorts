"""Produce a review-only 1080x1920 coffee-grounds Short with real Pexels B-roll and Gemini Charon.
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

ROOT = Path("out_coffee_grounds_short")
ROOT.mkdir(parents=True, exist_ok=True)
W,H = 1080,1920
RATE = 1.25
STOCK = [
    (27938388, "커피 가루 필터에 붓는 손 클로즈업", "https://www.pexels.com/video/pouring-coffee-grounds-into-filter-27938388/"),
    (6201662, "커피 가루가 포터필터에 떨어지는 장면", "https://www.pexels.com/video/coffee-grounds-falling-to-the-portafilter-6201662/"),
    (5540801, "핸드드립 커피 내리는 장면", "https://www.pexels.com/video/hot-water-getting-poured-on-ground-coffee-5540801/"),
    (7801575, "냉장고 문을 여는 장면", "https://www.pexels.com/video/woman-opening-the-refrigerator-7801575/"),
    (6160039, "퇴비를 손으로 섞는 장면", "https://www.pexels.com/video/organic-stuff-being-taken-from-basket-6160039/"),
    (5910449, "퇴비 유기물을 골라 섞는 장면", "https://www.pexels.com/video/sorting-out-compost-for-gardening-5910449/"),
    (9731959, "화분 흙 관리 장면", "https://www.pexels.com/video/people-loosening-the-soil-in-a-plant-pot-9731959/"),
    (5418706, "냉장고 내부 확인 장면", "https://www.pexels.com/video/a-woman-getting-food-from-a-refrigerator-5418706/"),
]
SCENES = [
    ("커피 마시고 남은 찌꺼기, 바로 버리시나요?", "커피 찌꺼기\n버리기 전에 보세요",0),
    ("먼저 꼭 알아둘 점! 젖은 찌꺼기는 오래 두면 곰팡이가 생길 수 있습니다.", "활용 전 주의!\n젖은 채 보관하지 않기",2),
    ("첫째, 바싹 말린 뒤 작은 그릇에 담아 냉장고 냄새 관리에 활용할 수 있어요.", "첫 번째 활용법\n말려서 냄새 관리",3),
    ("하지만 상한 음식처럼 냄새의 원인이 있다면, 먼저 치우는 게 중요합니다.", "냄새의 원인은\n먼저 제거하세요",7),
    ("둘째, 낙엽과 섞어 퇴비 재료로 사용할 수 있습니다.", "두 번째 활용법\n퇴비에 섞기",4),
    ("워싱턴 주립대는 퇴비 속 커피 찌꺼기를 전체의 이십 퍼센트 이하로 권장합니다.", "퇴비의 20% 이하\n적은 양만",5),
    ("반대로 화분에 두껍게 뿌리면 물과 공기의 흐름을 방해하고 식물에 해로울 수 있어요.", "화분에 두껍게?\n절대 금지",6),
    ("싱크대 배수구에도 버리지 마세요. 찌꺼기가 쌓이면 막힐 수 있습니다.", "배수구에 버리면\n막힐 위험",1),
    ("핵심은 충분한 건조, 적당한 양, 그리고 올바른 처리입니다.", "완전 건조 · 적당한 양\n배수구 투입 금지",0),
    ("도움이 됐다면 구독과 좋아요! 생활알고리즘.", "구독 · 좋아요\n생활알고리즘",None),
]
SOURCES = [
    "https://pubs.extension.wsu.edu/product/using-coffee-grounds-in-gardens-and-landscapes-home-garden-series/",
    "https://extension.sdstate.edu/spent-coffee-grounds-fertilizer-or-not",
    "https://integrishealth.org/resources/on-your-health/2022/august/creative-ways-to-use-old-coffee-grounds",
    "https://www.consumerreports.org/garbage-disposals/foods-you-can-cant-put-down-a-garbage-disposal-a1074300549/",
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
        d.rectangle((0,0,W,H),fill=(43,32,28,255))
        d.rounded_rectangle((100,520,980,1390),radius=56,fill=(250,248,239,255))
        d.text((540,650),"생활알고리즘",font=font(85),fill=(81,49,31),anchor="mm")
        d.text((540,950),"구독과 좋아요",font=font(84),fill=(116,65,42),anchor="mm")
        d.text((540,1190),"매일 쓸모 있는 생활정보",font=font(48),fill=(40,58,60),anchor="mm")
    else:
        d.rounded_rectangle((42,85,550,195),radius=30,fill=(53,35,27,235))
        d.text((296,142),"생활알고리즘",font=font(61),fill=(255,255,255),anchor="mm")
        d.rounded_rectangle((42,260,1038,470),radius=39,fill=(60,36,27,223))
        d.text((540,365),"커피 찌꺼기 활용법",font=font(75),fill=(252,252,250),anchor="mm")
        d.rounded_rectangle((35,1290,1045,1690),radius=44,fill=(39,24,20,238))
        lines=wrap_text(d,subtitle,83,910)
        if len(lines)>3:
            lines=wrap_text(d,subtitle,72,920)
        step=110
        top=1490-(len(lines)-1)*step/2
        for j,line in enumerate(lines):
            d.text((540,top+j*step),line,font=font(83 if len(lines)<=3 else 72),fill=(253,249,236),anchor="mm",stroke_width=0)
        d.rounded_rectangle((65,1790,1010,1810),radius=9,fill=(235,235,230,90))
        d.rounded_rectangle((65,1790,65+int(945*(index+1)/len(SCENES)),1810),radius=9,fill=(235,172,93,255))
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
                "color=c=0x342017:s=1080x1920:r=30","-t",f"{dur:.4f}",
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
    output=ROOT/"coffee_grounds_review_short.mp4"
    cmd("ffmpeg","-y","-hide_banner","-loglevel","error","-safe","0","-f","concat","-i",str(concat),
        "-c","copy","-movflags","+faststart",str(output))
    (ROOT/"captions.srt").write_text("\n".join(f"{i+1}\n{stamp(a)} --> {stamp(b)}\n{txt}\n"
      for i,(a,b,txt) in enumerate(timings)),encoding="utf-8")
    (ROOT/"script.txt").write_text("\n".join(line for line,_,_ in SCENES),encoding="utf-8")
    (ROOT/"sources_and_rights.txt").write_text("OFFICIAL FACT SOURCES\n"+"\n".join(SOURCES)+
       "\n\nPEXELS STOCK VIDEO CLIPS (Pexels License)\n"+
       "\n".join(f"{id} {label}: {url}; downloaded={id in usable}" for id,label,url in STOCK)+
       "\nhttps://www.pexels.com/legal-pages/license/\n"+
       "\nHuman review required: footage context, specific coffee grounds handling, sound and captions.\n",encoding="utf-8")
    (ROOT/"metadata.json").write_text(json.dumps({
        "title":"커피 찌꺼기 버리지 마세요! 활용법 2가지와 주의점 | 생활알고리즘 #shorts",
        "voice":"Gemini 2.5 Flash TTS Charon","speed":RATE,
        "duration_seconds":cursor,"resolution":"1080x1920",
        "real_footage_scene_count":len(SCENES)-1,
        "total_scenes":len(SCENES),
        "status":"DRAFT_REVIEW_REQUIRED",
        "youtube_uploaded":False,
        "usable_stock_ids":list(usable.keys()),
        "description":"사용한 커피 찌꺼기 활용법! 완전히 말려 냄새 관리에 쓰거나 적당량을 퇴비에 섞어보세요. 배수구에는 버리지 마세요. #생활알고리즘 #커피찌꺼기 #커피박 #생활정보 #shorts"
        },ensure_ascii=False,indent=2),encoding="utf-8")
    print("READY",output,"duration",cursor,flush=True)

if __name__=="__main__":
    asyncio.run(main())
