"""생활알고리즘 kimchi stain review: actual motion footage, Gemini Charon TTS, large captions.
Never uploads to YouTube; fail rather than fake moving clips with image zooms.
"""
from pathlib import Path
import os, subprocess, json, asyncio, wave, requests, zipfile
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
from gemini_charon_tts import speech
from kimchi_dishsoap_gemini_voice import TEXT

OUT = Path("kimchi_motion_review")
OUT.mkdir(exist_ok=True)
FF = imageio_ffmpeg.get_ffmpeg_exe()
W,H,FPS=720,1280,15
FONT="/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
if not Path(FONT).exists():
    FONT="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
if not Path(FONT).exists():
    fallback=OUT/"NanumGothic-Bold.ttf"
    url="https://raw.githubusercontent.com/google/fonts/main/ofl/nanumgothic/NanumGothic-Bold.ttf"
    resp=requests.get(url,timeout=35);resp.raise_for_status()
    fallback.write_bytes(resp.content)
    if fallback.stat().st_size < 100000:raise RuntimeError("Korean font download invalid")
    FONT=str(fallback)
# Pexels real-motion videos; no claims that the stock actors have used dish soap.
STOCK = {
 "soup":(6155936,"https://www.pexels.com/video/close-up-video-of-a-soup-6155936/"),
 "handwash":(6843718,"https://www.pexels.com/video/woman-doing-her-laundry-6843718/"),
 "laundry":(5592521,"https://www.pexels.com/video/person-pouring-laundry-detergent-5592521/"),
 "laundry2":(5592516,"https://www.pexels.com/video/woman-pouring-laundry-soap-on-a-washing-machine-5592516/"),
 "water":(855397,"https://www.pexels.com/video/hand-washing-855397/"),
}
# Sentence-by-sentence captions; emphasize FIRST pre-wash with dish soap before normal laundry.
SECTIONS=[
 ("김칫국물이 흰옷에 튀었다면?","문지르지 마세요!","soup",0.00,0.095),
 ("식당에서는 먼저","건더기를 걷고 톡톡 흡수","soup",0.095,0.19),
 ("물세탁 가능 여부 확인","얼룩 뒷면에서 찬물로 헹굼","water",0.19,0.36),
 ("여기서 가장 중요한 1차!","주방세제로 먼저 애벌빨래","handwash",0.36,0.51),
 ("주방세제는 소량만","손으로 부드럽게 애벌빨래","handwash",0.51,0.66),
 ("주방세제를 충분히 헹구고","2차! 세탁기로 일반 세탁","laundry",0.66,0.82),
 ("얼룩 남았으면","건조기 사용은 잠깐!","laundry2",0.82,0.915),
 ("생활알고리즘","구독과 좋아요!","laundry2",0.915,1.00),
]
CREDIT="Pexels free-use video. Source URLs in sources.txt; check current license before publishing."
def run(*args, timeout=180):
    return subprocess.run([FF,"-y","-hide_banner","-loglevel","error",*map(str,args)],
                          check=True,timeout=timeout,capture_output=True)
def font(sz):return ImageFont.truetype(FONT,sz)
def download(video_id):
    dest=OUT/f"stock_{video_id}.mp4"
    if dest.exists() and dest.stat().st_size>100000:return dest
    paths=[f"https://www.pexels.com/video/download/{video_id}/"]
    for size in ("720_1280","1280_720","1920_1080","1080_1920","540_960","960_540"):
        for fps in (25,30,24,50,60):
            paths.append(f"https://videos.pexels.com/video-files/{video_id}/{video_id}-hd_{size}_{fps}fps.mp4")
    session=requests.Session()
    session.headers["User-Agent"]="Mozilla/5.0 (educational Shorts video editor)"
    for url in paths:
        try:
            if url != paths[0]:
                h=session.head(url,timeout=5,allow_redirects=True)
                if h.status_code!=200 or "video" not in h.headers.get("content-type",""):continue
                if int(h.headers.get("content-length","0"))>65_000_000:continue
            with session.get(url,timeout=(8,45),stream=True) as resp:
                resp.raise_for_status()
                if not any(t in resp.headers.get("content-type","") for t in ("video","octet-stream")):continue
                size=0
                with dest.open("wb") as f:
                    for data in resp.iter_content(1024*1024):
                        if data:
                            size += len(data)
                            if size>65_000_000:raise RuntimeError("Stock video too large")
                            f.write(data)
            if dest.stat().st_size>100000:
                run("-i",dest,"-frames:v","1", "-f","null","-",timeout=30)
                print("VIDEO_OK",video_id, dest.stat().st_size,flush=True)
                return dest
        except Exception:dest.unlink(missing_ok=True)
    print("VIDEO_UNAVAILABLE",video_id,flush=True)
    return None
def caption_image(idx,t1,t2,duration):
    image=Image.new("RGBA",(W,H),(255,255,255,255))
    d=ImageDraw.Draw(image)
    # Unchanged channel style: white headline, central motion footage, white lower caption; no full-frame pan.
    d.rounded_rectangle((16,21,182,65),radius=12,fill="#172B35")
    d.text((99,43),"생활알고리즘",anchor="mm",font=font(23),fill="white")
    d.text((W//2,134),"흰옷에 김칫국물 묻었다면?",anchor="mm",font=font(41),fill="#1B2428")
    d.line((25,198,W-25,198),fill="#D4DBDD",width=3)
    # Actual footage window: y=212 through 862. All movement is inside that window.
    d.rounded_rectangle((19,886,W-19,1178),radius=26,fill="#F2F5F6")
    a,b,key,x,y=SECTIONS[idx]
    d.rounded_rectangle((37,900,169,946),radius=17,fill="#172B35")
    d.text((103,923),f"핵심 {idx+1:02}",anchor="mm",font=font(23),fill="white")
    headline_font=font(42)
    if len(a)>16:headline_font=font(35)
    d.text((360,988),a,font=headline_font,anchor="mm",fill="#263440")
    main_size=48 if len(b)<=16 else 42
    maincolor="#C52339" if idx in (3,4,5) else "#182833"
    d.text((360,1075),b,font=font(main_size),anchor="mm",fill=maincolor)
    if idx in (3,4):
        d.rounded_rectangle((207,1112,513,1164),radius=15,fill="#FFE58F")
        d.text((360,1138),"세탁기 전에 반드시!",anchor="mm",font=font(23),fill="#25333B")
    if idx==7:
        d.rounded_rectangle((210,1113,510,1164),radius=16,fill="#FFE58F")
        d.text((360,1139),"구독 · 좋아요",anchor="mm",font=font(25),fill="#162A36")
    d.text((26,1218),"생활알고리즘 | 알아두면 쓸모 있는 생활정보",font=font(18),fill="#79848B")
    d.rounded_rectangle((22,1260,698,1266),radius=3,fill="#E7E4E1")
    d.rounded_rectangle((22,1260,22+int(676*t2),1266),radius=3,fill="#DF5E83")
    save=OUT/f"caption_{idx:02}.png";image.save(save);return save
def fetch_cached_voice(dest):
    # Already generated in earlier successful Gemini Charon voice workflow.
    # This avoids a second paid TTS call for the exact same approved narration.
    token=os.environ.get("GH_ACTION_TOKEN")
    if not token:raise RuntimeError("GITHUB_TOKEN required to reuse existing Charon audio")
    url="https://api.github.com/repos/rironim-arch/iro_shorts/actions/artifacts/13927834734/zip"
    response=requests.get(url,headers={"Authorization":"Bearer "+token,
        "Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"},timeout=45)
    response.raise_for_status()
    with zipfile.ZipFile(BytesIO(response.content)) as archive:
        name=next((n for n in archive.namelist() if n.endswith("kimchi_charon_raw.wav")),None)
        if not name:raise RuntimeError("Existing Gemini Charon raw WAV not in artifact")
        dest.write_bytes(archive.read(name))
    if dest.stat().st_size<100000:raise RuntimeError("Previously generated Charon audio invalid")
    print("CACHED_CHARON_AUDIO_REUSED",dest.stat().st_size,flush=True)
async def main():
    (OUT/"sources.txt").write_text(CREDIT+"\n"+"\n".join(v[1] for v in STOCK.values()),encoding="utf-8")
    raw=OUT/"raw_charon.wav"
    fetch_cached_voice(raw)
    sound=OUT/"charon_125.wav"
    run("-i",raw,"-af","atempo=1.25","-ar","24000","-ac","1",sound)
    with wave.open(str(sound),"rb") as w:duration=w.getnframes()/w.getframerate()
    print("VOICE_LENGTH",duration,flush=True)
    # Get real moving stock clips. Do not produce a pan/zoom slideshow as fallback.
    files={k:download(v[0]) for k,v in STOCK.items()}
    if not files["handwash"] or not files["laundry"]:
        raise RuntimeError("Real fabric-washing/laundry stock video unavailable; refuse photo-pan substitute.")
    if not files["soup"]:files["soup"]=files["handwash"]
    if not files["water"]:files["water"]=files["handwash"]
    if not files["laundry2"]:files["laundry2"]=files["laundry"]
    chapters=[];subtitles=[]
    for i,(a,b,key,st,en) in enumerate(SECTIONS):
        dt=(en-st)*duration
        caption=caption_image(i,st,en,duration)
        src=files[key]
        output=OUT/f"part_{i:02}.mp4"
        # Source footage has genuine subject movement. The video window never pans/zooms.
        vf="[0:v]scale=720:650:force_original_aspect_ratio=increase,crop=720:650,fps=15,pad=720:1280:0:212:color=white[bg];[bg][1:v]overlay=0:0:shortest=1,format=yuv420p[out]"
        run("-stream_loop","-1","-i",src,"-loop","1","-i",caption,
            "-filter_complex",vf,"-map","[out]","-an","-t",f"{dt:.3f}",
            "-c:v","libx264","-preset","ultrafast","-crf","24",
            "-r",str(FPS),output,timeout=100)
        chapters.append(output)
        def tc(t):
            ms=round(t*1000); hh,ms=divmod(ms,3600000);mm,ms=divmod(ms,60000);ss,ms=divmod(ms,1000)
            return f"{hh:02}:{mm:02}:{ss:02},{ms:03}"
        subtitles.append(f"{i+1}\n{tc(st*duration)} --> {tc(en*duration)}\n{a}\n{b}\n")
        print("SECTION",i+1,dt,flush=True)
    concat=OUT/"parts.txt"
    concat.write_text("\n".join("file '"+str(p.resolve())+"'" for p in chapters),encoding="utf8")
    video=OUT/"all_silent.mp4"
    run("-f","concat","-safe","0","-i",concat,"-c:v","copy",video,timeout=150)
    final=OUT/"kimchi_corrected_charon_motion.mp4"
    run("-i",video,"-i",sound,"-map","0:v:0","-map","1:a:0",
        "-c:v","copy","-c:a","aac","-b:a","128k","-t",f"{duration:.3f}",
        "-movflags","+faststart",final,timeout=100)
    (OUT/"subtitles.srt").write_text("\n".join(subtitles),encoding="utf-8")
    (OUT/"script.txt").write_text(TEXT,encoding="utf-8")
    (OUT/"quality.json").write_text(json.dumps({"duration":duration,"voice":"Gemini 2.5 Flash TTS / Charon","speed":1.25,
       "real_footage_used":{k:str(v) if v else None for k,v in files.items()},
       "headline_style":"legacy white title + central moving action + bottom captions",
       "priority_step":"FIRST pre-treat with a SMALL AMOUNT of dish soap by gentle hand wash; rinse; THEN regular machine wash",
       "manually_review_required":True,"youtube_uploaded":False},ensure_ascii=False,indent=2))
    print("RENDER_OK",final.stat().st_size,"bytes",flush=True)
if __name__=="__main__":
    asyncio.run(main())
