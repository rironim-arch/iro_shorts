"""아들러 심리학 01 | 생활알고리즘 | 검토용 Gemini Charon 영상."""
import json, os, re, subprocess, time, wave
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw, ImageFont

W,H=1080,1920
OUT=Path("output_adler_01"); OUT.mkdir(exist_ok=True)
BEATS=[
("착한 사람은 왜 항상 상처받을까요?","착한 사람은 왜\n늘 상처받을까?","hero"),
("어쩌면 착해서가 아니라, 거절하면 미움받을까 봐 두려운 걸지도 모릅니다.","거절하면 미움받을까\n두려운 걸까요?","person"),
("퇴근하기 10분 전, 동료가 말합니다. 이것만 좀 대신해 줄래?","퇴근 10분 전\n또 부탁이 옵니다","office"),
("오늘은 정말 쉬고 싶지만, 결국 웃으며 대답하죠. 네, 제가 할게요.","쉬고 싶은데도\n\"네, 제가 할게요\"","office"),
("집에 돌아와서야 화가 납니다. 왜 항상 나만 양보하는 거지?","왜 항상 나만\n양보하는 걸까?","home"),
("아들러 심리학을 이해하는 중요한 관점 중 하나가 과제의 분리입니다.","아들러 심리학\n과제의 분리","split"),
("상대가 부탁하는 건 상대의 선택입니다. 하지만 들어줄지 결정하는 건 나의 선택입니다.","상대의 부탁과\n나의 선택은 다릅니다","split"),
("내가 거절하면 상대가 서운할 수 있어요. 그렇다고 그 감정을 전부 책임질 필요는 없습니다.","상대의 감정까지\n책임질 필요는 없어요","split"),
("다음에는 이렇게 말해 보세요. 오늘은 어렵습니다. 내일 도와드릴게요.","\"오늘은 어렵습니다\"\n괜찮은 한마디","office"),
("거절은 무례함이 아닙니다. 나의 시간과 마음을 존중하는 행동입니다.","거절은 무례함이 아닌\n자기 존중입니다","heart"),
("친절은 지키되, 내 삶의 선택권까지 내어주지는 마세요.","친절하되\n나를 잃지는 마세요","split"),
("좋은 사람이 되는 것과 나를 희생하는 것은 다릅니다.","좋은 사람과\n희생하는 사람은 달라요","split"),
("모두에게 좋은 사람일 필요는 없습니다. 나에게도 좋은 사람이 되어 주세요.","나에게도 좋은 사람이\n되어 주세요","person"),
("생활알고리즘. 공감했다면 구독과 좋아요로 함께해 주세요.","생활알고리즘\n구독 · 좋아요","brand")]
INK="#25262D"; CREAM="#F7F0E7"; CORAL="#E8755B"; SAGE="#98B49D"; GOLD="#EFBF62"; PAPER="#FFFDF8"; DARK="#282A32"

def run(*args):
    subprocess.run(args,check=True)

def font(size,bold=True):
    paths=(
      ["/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc","/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc","C:/Windows/Fonts/malgunbd.ttf"]
      if bold else
      ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc","/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc","C:/Windows/Fonts/malgun.ttf"])
    for p in paths:
        if Path(p).exists(): return ImageFont.truetype(p,size)
    raise RuntimeError("Korean font not found")

def rrect(d,b,fill,r=32,outline=None,w=2):
    d.rounded_rectangle(b,fill=fill,radius=r,outline=outline,width=w)

def center(d,xy,txt,sz=64,col=INK):
    d.text(xy,txt,font=font(sz),fill=col,anchor="mm")

def person(d,cx=540,cy=660,s=1.5,sad=False,shirt="#F0BC78"):
    r=int(98*s)
    d.ellipse((cx-r,cy-r,cx+r,cy+r),fill="#E7B58D")
    d.pieslice((cx-r,cy-r-30,cx+r,cy+30),180,352,fill="#353E44")
    for dx in [-25,25]:
        ey=cy+int(3*s)
        d.ellipse((cx+int(dx*s)-7,ey-6,cx+int(dx*s)+7,ey+6),fill="#353E44")
    box=(cx-int(20*s),cy+int(30*s),cx+int(20*s),cy+int(65*s))
    d.arc(box,180 if sad else 0,355 if sad else 180,fill="#353E44",width=5)
    d.rounded_rectangle((cx-int(170*s),cy+int(94*s),cx+int(170*s),cy+int(373*s)),radius=int(120*s),fill=shirt)

def draw_visual(d,scene,dark):
    if scene in ("hero","person","home"):
        if scene=="home":
            rrect(d,(120,470,960,1135),"#45444B",55)
            d.ellipse((735,500,875,640),fill=GOLD)
            person(d,540,670,1.30,True,shirt="#A9A0A2")
            d.rectangle((160,1055,915,1115),fill="#706269")
        else:
            d.ellipse((170,380,910,1120),fill=CORAL if scene=="hero" else "#E4D5CE")
            person(d,540,655,1.70,scene!="hero",shirt="#F0BC78" if scene=="hero" else SAGE)
            if scene=="hero":
                for x,y in [(200,575),(875,760),(175,950)]:
                    d.line((x,y,x-40,y+95),fill="#FBE1CD",width=12)
    elif scene=="office":
        rrect(d,(115,475,965,1160),"#E2D6CB",45)
        d.rectangle((175,915,910,965),fill="#72625A")
        d.rectangle((230,965,265,1115),fill="#72625A")
        d.rectangle((835,965,870,1115),fill="#72625A")
        rrect(d,(275,690,650,930),"#353E44",24)
        rrect(d,(295,712,630,888),"#BBD0CD",15)
        person(d,780,680,.75,True,shirt="#789AA5")
        rrect(d,(135,440,580,600),PAPER,39)
        center(d,(355,518),"10분 전 부탁!",52)
    elif scene=="split":
        d.line((540,435,540,1090),fill=GOLD if dark else CORAL,width=15)
        rrect(d,(95,515,505,1060),"#4B4D56" if dark else "#E6D9CC",45)
        rrect(d,(575,515,985,1060),"#5B555E" if dark else "#D8E3D9",45)
        center(d,(300,665),"상대",94,"#FFFFFF" if dark else INK)
        center(d,(780,665),"나",104,"#FFFFFF" if dark else INK)
        center(d,(300,850),"부탁·감정",52,GOLD if dark else CORAL)
        center(d,(780,850),"선택·시간",52,GOLD if dark else CORAL)
    elif scene=="heart":
        d.ellipse((200,390,880,1090),fill=SAGE)
        d.ellipse((318,640,557,900),fill=PAPER)
        d.ellipse((522,640,761,900),fill=PAPER)
        d.polygon([(327,794),(750,794),(542,1075)],fill=PAPER)
    elif scene=="brand":
        d.ellipse((172,375,908,1120),fill=GOLD)
        center(d,(540,650),"생활",125)
        center(d,(540,830),"알고리즘",118)

def draw_frame(i,beat):
    narration,caption,scene=beat
    dark=i in (0,4,5,7,10)
    bg=DARK if dark else CREAM
    im=Image.new("RGB",(W,H),bg);d=ImageDraw.Draw(im)
    if dark:
        d.ellipse((-280,260,770,1300),fill="#393940")
        d.ellipse((570,-260,1320,500),fill="#45424B")
    else:
        d.ellipse((565,-250,1320,510),fill="#F1DCC7")
        d.ellipse((-300,720,385,1600),fill="#EEDBCF")
    rrect(d,(58,65,565,185),CORAL,45)
    center(d,(312,124),"생활알고리즘",64,"#FFFFFF")
    rrect(d,(686,72,1020,178),"#56535A" if dark else "#E3D6CB",38)
    center(d,(852,126),"심리학 · 01",42,"#FFFFFF" if dark else INK)
    d.text((78,273),"ADLER  /  PSYCHOLOGY",font=font(38,False),fill=GOLD if dark else CORAL)
    draw_visual(d,scene,dark)
    rrect(d,(49,1230,1032,1702),PAPER,53)
    rrect(d,(73,1260,91,1664),CORAL,8)
    lines=caption.split("\n")
    sz=80
    while sz>56:
        f=font(sz)
        if all(d.textbbox((0,0),line,font=f)[2] <=830 for line in lines):break
        sz-=2
    for j,line in enumerate(lines): center(d,(550,1403+j*130),line,sz)
    d.text((68,1770),"사람과 관계를 이해하는 1분",font=font(37,False),fill="#FFFFFF" if dark else INK)
    d.text((1013,1772),f"{i+1:02} / {len(BEATS):02}",font=font(37,False),fill="#FFFFFF" if dark else INK,anchor="ra")
    rrect(d,(66,1840,1015,1856),"#68636A" if dark else "#D8D0C9",8)
    rrect(d,(66,1840,66+round(949*(i+1)/len(BEATS)),1856),CORAL,8)
    im.save(OUT/f"frame_{i:02}.png",optimize=True)

def pcm_to_wav(data,mime,path):
    if data[:4]==b"RIFF" or "wav" in mime:
        path.write_bytes(data);return
    if mime and "pcm" not in mime and "l16" not in mime:raise ValueError("Unexpected audio MIME "+mime)
    match=re.search(r"rate=(\d+)",mime)
    rate=int(match.group(1)) if match else 24000
    with wave.open(str(path),"wb") as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes(data)

def gen_voice(client,i,sentence):
    from google.genai import types
    prompt=("Speak ONLY this Korean narration, with a calm, warm, clear mature male voice. "
      "Natural Korean cadence, a little compassionate drama, no extra words, no background sound. "
      "This is short-form psychology narration:\n\n"+sentence)
    for attempt in range(5):
        try:
            response=client.models.generate_content(
                model=os.getenv("GEMINI_TTS_MODEL","gemini-2.5-flash-preview-tts"),
                contents=prompt,
                config=types.GenerateContentConfig(response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
            part=next(p.inline_data for p in response.candidates[0].content.parts if getattr(p,"inline_data",None))
            dest=OUT/f"raw_{i:02}.wav"
            pcm_to_wav(part.data,(part.mime_type or "").lower(),dest)
            return dest
        except Exception as exc:
            if attempt==4:raise
            sleep=12*(attempt+1)
            print(f"TTS retry {i+1}, {sleep}s: {str(exc)[:150]}",flush=True)
            time.sleep(sleep)

def duration(path):
    p=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=noprint_wrappers=1:nokey=1",str(path)],capture_output=True,text=True,check=True)
    return float(p.stdout.strip())

def timestamp(sec):
    ms=round(sec*1000)
    h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def main():
    from google import genai
    key=os.getenv("GEMINI_API_KEY")
    if not key:raise RuntimeError("GEMINI_API_KEY secret missing")
    client=genai.Client(api_key=key)
    # One Gemini request per pair of scenes, staying below the free-tier
    # 10-requests-per-day cap. Exact pair duration, approximate split inside pair.
    durations=[0.0]*len(BEATS)
    groups=[list(range(i,min(i+2,len(BEATS)))) for i in range(0,len(BEATS),2)]
    for gi,indices in enumerate(groups):
        spoken=" ".join(BEATS[i][0] for i in indices)
        raw=gen_voice(client,gi,spoken)
        processed=OUT/f"audio_group_{gi:02}.wav"
        run("ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(raw),
            "-filter:a","atempo=1.25","-ac","1","-ar","24000",str(processed))
        group_duration=duration(processed)
        weights=[max(1,len(re.sub(r"\\s+","",BEATS[i][0]))) for i in indices]
        for i,w in zip(indices,weights):
            durations[i]=group_duration*w/sum(weights)
        print(f"Voice group {gi+1}/{len(groups)} duration={group_duration:.2f}s",flush=True)
        time.sleep(7)
    for i,beat in enumerate(BEATS):
        draw_frame(i,beat)
        print(f"Rendered scene {i+1}/{len(BEATS)}",flush=True)
    (OUT/"script.txt").write_text("\n".join(b[0] for b in BEATS),encoding="utf-8")
    meta={"title":"착한 사람은 왜 항상 상처받을까? | 아들러 심리학 1화 #shorts",
          "description":"아들러 심리학을 참고해 만든 일상 심리 해설입니다. #생활알고리즘 #아들러심리학 #shorts",
          "voice":"Gemini 2.5 Flash TTS / Charon","speed":1.25,
          "status":"DRAFT_REVIEW_REQUIRED","uploaded_to_youtube":False,
          "caption_sync":"Exact voice timing per two-scene group; estimated split within each group.",
          "note":"아들러의 직접 인용이 아닌 재구성한 내용",
          "generated_at_kst":datetime.now(ZoneInfo("Asia/Seoul")).isoformat()}
    (OUT/"metadata.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
    srt=[];t=0.
    for i,(b,dur) in enumerate(zip(BEATS,durations)):
        srt.append(f"{i+1}\n{timestamp(t)} --> {timestamp(t+dur)}\n{b[0]}\n");t+=dur
    (OUT/"captions.srt").write_text("\n".join(srt),encoding="utf-8")
    vf=[];af=[]
    for i,dur in enumerate(durations):
        vf.extend([f"file 'frame_{i:02}.png'",f"duration {dur:.6f}"])
    for gi in range(len(groups)):
        af.append(f"file 'audio_group_{gi:02}.wav'")
    vf.append(f"file 'frame_{len(BEATS)-1:02}.png'")
    (OUT/"video_slides.txt").write_text("\n".join(vf)+"\n",encoding="utf-8")
    (OUT/"audio_clips.txt").write_text("\n".join(af)+"\n",encoding="utf-8")
    run("ffmpeg","-y","-hide_banner","-loglevel","error","-safe","0","-f","concat",
        "-i",str(OUT/"audio_clips.txt"),"-c:a","pcm_s16le",str(OUT/"voice_full.wav"))
    run("ffmpeg","-y","-hide_banner","-loglevel","error","-safe","0","-f","concat",
        "-i",str(OUT/"video_slides.txt"),"-i",str(OUT/"voice_full.wav"),
        "-map","0:v:0","-map","1:a:0","-vf","fps=30,format=yuv420p",
        "-c:v","libx264","-preset","veryfast","-crf","23",
        "-c:a","aac","-b:a","128k","-t",f"{t:.4f}",
        "-movflags","+faststart",str(OUT/"adler_psychology_01.mp4"))
    print(f"Done. {t:.1f}s review video produced, no YouTube upload.",flush=True)
if __name__=="__main__":main()
