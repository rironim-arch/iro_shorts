"""생활알고리즘: sourced educational Shorts with differentiated editorial layouts.
Manual workflow generates a draft only. It NEVER uploads to YouTube.
"""
import asyncio, json, os, math, subprocess
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw, ImageFont
from editorial_quality import run_review, OUT
from gemini_charon_tts import speech

W,H=1080,1920
INK="#29343A"; PAPER="#F8F5EE"; WHITE="#FFFFFF"; BLACK="#1C2428"
COLORS={
 "warning":{"base":"#FFF4EC","hero":"#DC6546","accent":"#F8BA74","deep":"#51312A"},
 "myth":{"base":"#F0F7FB","hero":"#427FA3","accent":"#ECA563","deep":"#24475E"},
 "checklist":{"base":"#EFF8F1","hero":"#398975","accent":"#E8B85F","deep":"#25594E"},
 "comparison":{"base":"#F5F2FC","hero":"#7963A4","accent":"#F2C167","deep":"#4C4072"}
}
VOICE="Gemini 2.5 Flash TTS / Charon"
RATE=1.25

def run(*args):
    subprocess.run(args,check=True)

def fnt(size,bold=True):
    faces=["/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
      "C:/Windows/Fonts/malgunbd.ttf" if bold else "C:/Windows/Fonts/malgun.ttf"]
    for path in faces:
        if Path(path).exists():
            return ImageFont.truetype(path,size)
    raise RuntimeError("No CJK font")

def rect(d,xy,fill,r=32,outline=None,width=2):
    d.rounded_rectangle(tuple(map(int,xy)),radius=r,fill=fill,outline=outline,width=width)

def label(d,xy,s,size=58,color=INK,center=False):
    d.text(xy,s,font=fnt(size),fill=color,anchor="mm" if center else None)

def lines_for(d,s,sz,maxw):
    out=[];words=s.split();cur=""
    for word in words:
        new=(cur+" "+word).strip()
        if d.textbbox((0,0),new,font=fnt(sz))[2]<=maxw:
            cur=new
        else:
            if cur:out.append(cur)
            cur=word
    if cur:out.append(cur)
    return out or [s]

def wrapped(d,txt,center_x,center_y,maxw,desired=85,max_lines=3,color=INK):
    for sz in range(desired,48,-2):
        lines=lines_for(d,txt,sz,maxw)
        if len(lines)<=max_lines: break
    space=sz+30
    start=center_y-(len(lines)-1)*space/2
    for i,line in enumerate(lines):
        label(d,(center_x,start+i*space),line,sz,color,True)

def scene_diagram(d,topic,i,p):
    """Topic-dependent diagrams, not stock or templated 'did you know' backgrounds."""
    style=topic["format"];cx=540
    card=(90,440,990,1150)
    rect(d,card,WHITE,48)
    hero=p["hero"];accent=p["accent"];deep=p["deep"]
    d.ellipse((190,490,895,1090),fill=p["base"])
    if style=="warning":
        # Two incompatible bottles, slash and safety alert.
        for x,fl in [(255,hero),(625,accent)]:
            rect(d,(x,700,x+210,945),fl,28)
            rect(d,(x+56,645,x+158,716),fl,14)
            rect(d,(x+30,770,x+180,855),WHITE,15)
            label(d,(x+105,812),"세정제",40,deep,True)
        d.line((255,990,855,560),fill=hero,width=28)
        d.ellipse((722,534,865,677),fill=hero)
        label(d,(792,607),"!",98,WHITE,True)
        if i in (2,3):
            for dx,dy in [(438,600),(525,550),(615,610)]:
                d.arc((dx-50,dy-70,dx+50,dy+90),190,355,fill=hero,width=10)
    elif style=="myth":
        rect(d,(220,590,860,1010),"#C9DFED",50)
        rect(d,(280,650,800,908),WHITE,22)
        d.ellipse((475,718,606,849),outline=deep,width=16)
        d.ellipse((505,748,576,819),outline=deep,width=12)
        rect(d,(340,920,745,967),hero,15)
        if i in (0,2,3):
            d.line((300,550,790,1040),fill=accent,width=24)
        if i in (4,5):
            rect(d,(260,502,820,602),accent,20)
            label(d,(540,552),"사용설명서",57,BLACK,True)
    elif style=="checklist":
        rect(d,(325,546,755,1070),"#E4F1EB",48)
        rect(d,(390,600,690,1010),WHITE,18)
        d.line((400,755,680,755),fill=hero,width=7)
        d.line((400,850,680,850),fill=hero,width=7)
        label(d,(540,685),"4℃",112,deep,True)
        if i in (3,4,5):
            for y in (797,896,984):
                d.ellipse((755,y-24,803,y+24),fill=hero)
                label(d,(778,y),"✓",38,WHITE,True)
    elif style=="comparison":
        rect(d,(193,640,888,1020),"#E6DDF5",42)
        rect(d,(245,695,840,971),WHITE,30)
        for ix in range(4):
            x=310+(ix%2)*300;y=750+(ix//2)*128
            d.ellipse((x-36,y-36,x+36,y+36),outline=hero,width=12)
            d.ellipse((x+60,y-36,x+132,y+36),outline=hero,width=12)
        d.line((200,587,880,587),fill=accent,width=32)
        label(d,(540,540),"정격 확인",67,deep,True)
        if i in (2,5):
            d.ellipse((695,835,920,1060),fill=hero)
            label(d,(805,941),"!",94,WHITE,True)

def render(topic,i):
    p=COLORS[topic["format"]]
    im=Image.new("RGB",(W,H),p["base"])
    d=ImageDraw.Draw(im)
    d.ellipse((-240,-200,440,460),fill="#FFFFFF")
    d.ellipse((790,1200,1410,1940),fill="#FFFFFF")
    rect(d,(60,65,528,170),p["deep"],35)
    label(d,(293,118),"생활알고리즘",59,WHITE,True)
    rect(d,(700,72,1010,163),p["accent"],30)
    label(d,(855,117),topic["category"],43,BLACK,True)
    wrapped(d,topic["title"],540,330,870,65,2,p["deep"])
    scene_diagram(d,topic,i,p)
    # Narrative-specific middle card, big type, safe for Shorts UI.
    rect(d,(60,1210,1020,1655),WHITE,50)
    rect(d,(80,1230,99,1630),p["hero"],8)
    label(d,(138,1285),f"POINT {i+1:02}",45,p["hero"])
    wrapped(d,topic["visuals"][i],553,1450,790,86,3,BLACK)
    label(d,(72,1754),"오늘 바로 써먹는 생활정보",37,INK)
    d.text((1004,1754),f"{i+1:02} / {len(topic['scripts']):02}",font=fnt(37),fill=INK,anchor="ra")
    rect(d,(73,1823,1007,1845),"#DCD8D3",9)
    rect(d,(73,1823,73+934*(i+1)/len(topic["scripts"]),1845),p["hero"],9)
    file=OUT/f"scene_{i:02}.png";im.save(file)
    return file

def duration(file):
    r=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=noprint_wrappers=1:nokey=1",str(file)],capture_output=True,text=True,check=True)
    return float(r.stdout.strip())

def timecode(sec):
    ms=round(1000*sec)
    h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


async def main():
    topics=run_review()
    tid=int(os.getenv("TOPIC_ID",101))
    index={item["id"]:item for item in topics}
    if tid not in index:raise ValueError(f"Unknown curated TOPIC_ID {tid}")
    topic=index[tid]
    runtime=[];audio_names=[]
    for i,text in enumerate(topic["scripts"]):
        render(topic,i)
        raw_wav=OUT/f"raw_audio_{i:02}.wav"
        await speech(text,raw_wav)
        wav=OUT/f"audio_{i:02}.wav"
        run("ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(raw_wav),
            "-af","atempo=1.25","-ar","24000","-ac","1",str(wav))
        runtime.append(duration(wav))
        audio_names.append(wav)
        print(f"Scene {i+1}/{len(topic['scripts'])} narrated, {runtime[-1]:.1f}s",flush=True)
    t=0.;vlist=[];alist=[];srts=[]
    for i,(text,dt) in enumerate(zip(topic["scripts"],runtime)):
        vlist.extend([f"file 'scene_{i:02}.png'",f"duration {dt:.6f}"])
        alist.append(f"file 'audio_{i:02}.wav'")
        srts.append(f"{i+1}\n{timecode(t)} --> {timecode(t+dt)}\n{text}\n")
        t+=dt
    vlist.append(f"file 'scene_{len(topic['scripts'])-1:02}.png'")
    (OUT/"frames.txt").write_text("\n".join(vlist)+"\n",encoding="utf-8")
    (OUT/"audios.txt").write_text("\n".join(alist)+"\n",encoding="utf-8")
    (OUT/"captions.srt").write_text("\n".join(srts),encoding="utf-8")
    (OUT/"script.txt").write_text(topic["title"]+"\n\n"+"\n".join(topic["scripts"]),encoding="utf-8")
    (OUT/"sources.txt").write_text(topic["source_name"]+"\n"+topic["source_url"]+"\n\n편집 검토 필요",encoding="utf-8")
    metadata={
        "title":topic["title"]+" | 생활알고리즘 #shorts",
        "description":"생활에 바로 적용하는 핵심 정보.\n출처: "+topic["source_url"]+"\n#생활알고리즘 #생활상식 #shorts",
        "format":topic["format"],"topic_id":tid,"source_url":topic["source_url"],
        "status":"DRAFT_REVIEW_REQUIRED","youtube_uploaded":False,
        "manual_review_required":True,"AI_narration":VOICE,"speed":RATE,
        "sync":"Each scene's duration is measured from its own TTS audio.",
        "generated_at_kst":datetime.now(ZoneInfo("Asia/Seoul")).isoformat()
    }
    (OUT/"metadata.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding="utf-8")
    run("ffmpeg","-y","-hide_banner","-loglevel","error","-safe","0","-f","concat",
        "-i",str(OUT/"audios.txt"),"-c:a","pcm_s16le",str(OUT/"narration.wav"))
    run("ffmpeg","-y","-hide_banner","-loglevel","error","-safe","0","-f","concat",
        "-i",str(OUT/"frames.txt"),"-i",str(OUT/"narration.wav"),
        "-map","0:v:0","-map","1:a:0","-vf","fps=30,format=yuv420p",
        "-c:v","libx264","-preset","veryfast","-crf","23","-c:a","aac","-b:a","128k",
        "-t",f"{t:.5f}","-movflags","+faststart",str(OUT/"review_short.mp4"))
    print(f"Draft created: {t:.1f}s, no YouTube upload",flush=True)
if __name__=="__main__":
    asyncio.run(main())
