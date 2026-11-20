"""Review-only 생활알고리즘 Shorts: white header / real licensed photos / Gemini Charon Korean TTS."""
import os, re, io, json, time, wave, subprocess
from pathlib import Path
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from google import genai
from google.genai import types

OUT=Path("powerstrip_boiler_exports");OUT.mkdir(exist_ok=True)
W,H=720,1280
NAVY="#19334D";YELLOW="#FFE05A";CREAM="#FFFDF9";WHITE="#FFFFFF"
R=requests.Session()
R.headers["User-Agent"]="Mozilla/5.0"
CFG={
 "powerstrip":{
  "headline":["멀티탭에 이거 꽂으면","정말 위험할까요?"],
  "filename":"01_powerstrip_gemini_charon.mp4",
  "photos":[15000981,18358118,14071432,4943088,9696590,5691590,36738243,15000981],
  "lines":[
    "집에 있는 멀티탭, 지금 뭐가 꽂혀 있나요? 구멍이 많다고 전부 안전한 건 아닙니다.",
    "멀티탭 하나에 충전기를 다섯 개 꽂아도 큰 문제가 없을 수 있어요. 그런데 두 개만 꽂았는데도 위험해지는 상황이 있습니다.",
    "차이는 바로 소비전력입니다. 사용 중인 제품의 소비전력을 모두 합한 값이 멀티탭의 정격용량을 넘는지 확인해야 합니다.",
    "예를 들어 소비전력 이천 와트짜리 난방기와 천오백 와트짜리 전기포트를 동시에 켠다면, 합계는 삼천오백 와트가 됩니다.",
    "멀티탭이 감당할 수 있는 용량을 넘기면 전선과 접속부가 과열될 수 있고, 잘못된 사용은 화재로 이어질 수도 있습니다.",
    "그래서 특히 조심할 제품은 전기히터 같은 고출력 온열기와 일부 에어컨입니다. 멀티탭에 여러 개를 이어서 꽂는 방식도 피해야 합니다.",
    "이런 고출력 가전은 제품 안내에 따라 적합한 벽면 콘센트에 단독 연결하고, 멀티탭에 적힌 정격과 코드 손상 여부를 확인하세요.",
    "플러그에서 타는 냄새가 나거나 비정상적으로 뜨거워진다면 사용을 중단하세요. 생활알고리즘, 구독과 좋아요!"
  ],
  "urls":[
    "https://www.kats.go.kr/",
    "https://www.kca.go.kr/",
    "https://www.pexels.com/license/"
  ]
 },
 "boiler":{
  "headline":["보일러 외출모드","매일 누르면 손해일까?"],
  "filename":"02_boiler_away_mode_gemini_charon.mp4",
  "photos":[15377743,7616651,36818203,34558052,12644994,7616651,15377743,17854890],
  "lines":[
    "출근할 때마다 보일러 외출 버튼을 누르시나요? 무조건 난방비가 줄어든다고 생각하면 오해일 수 있습니다.",
    "외출모드라는 이름은 같아도 모든 보일러가 똑같이 움직이지 않습니다. 어떤 제품은 난방을 크게 줄이고 동파 방지 중심으로 작동하거든요.",
    "또 우리 집이 개별난방인지 지역난방인지에 따라 적절한 조절 방법도 달라질 수 있습니다. 여기서 중요한 건 외출 시간이에요.",
    "잠깐 집을 비우는데 실내 온도를 지나치게 낮추면, 다시 따뜻하게 만드는 데 시간이 오래 걸리고 쾌적함도 떨어질 수 있습니다.",
    "지역난방이라면 짧은 외출 때 난방을 완전히 끄기보다 설정 온도를 평소보다 이 도에서 삼 도 정도 낮추는 방식이 안내됩니다.",
    "반면 개별 가스보일러는 모델에 따라 외출모드 기능이 다릅니다. 모든 집에 같은 절약 공식이 적용되는 건 아니에요.",
    "외출모드가 동파 방지만 하는지, 최저 난방을 유지하는지 사용설명서에서 확인하고, 집의 단열과 외출 시간도 함께 고려하세요.",
    "특히 한파에는 장시간 전원을 완전히 끄는 행동이 동파 위험을 높일 수 있습니다. 생활알고리즘, 구독과 좋아요!"
  ],
  "urls":[
    "https://www.energy.or.kr/",
    "https://www.kdnavien.co.kr/",
    "https://www.rinnai.co.kr/",
    "https://www.pexels.com/license/"
  ]
 }
}
def ff(*args):
    subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error",*map(str,args)],check=True,timeout=240)
def font_path():
    for p in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc","/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc","/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"]:
        if Path(p).exists():return p
    raise RuntimeError("Korean Noto font unavailable")
FONT=font_path()
def f(size):return ImageFont.truetype(FONT,size)
def wavduration(path):
    with wave.open(str(path),"rb") as w:return w.getnframes()/w.getframerate()
def normalized(txt):return re.sub(r"[^0-9A-Za-z가-힣]","",txt)
def photos(key,ids):
    pics=[];sources=[]
    for i,id in enumerate(ids):
        p=OUT/f"{key}_photo{i:02}.jpg"
        try:
            url=f"https://images.pexels.com/photos/{id}/pexels-photo-{id}.jpeg?auto=compress&cs=tinysrgb&w=1100"
            resp=R.get(url,timeout=(7,26));resp.raise_for_status()
            im=Image.open(io.BytesIO(resp.content)).convert("RGB")
            if min(im.size)<400:raise ValueError("photo too small")
            im.save(p,quality=87)
            pics.append(p);sources.append(f"https://www.pexels.com/photo/{id}/")
        except Exception as exc:
            print("PHOTO_FALLBACK",id,str(exc)[:80],flush=True)
            pics.append(None)
    usable=[p for p in pics if p]
    if len(usable)<3:raise RuntimeError("Not enough licensed photographs")
    for i,p in enumerate(pics):
        if p is None:pics[i]=usable[i%len(usable)]
    return pics,sources
def audio(key,lines):
    client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    script="\n".join(lines)
    prompt=("Korean male voiceover for a trustworthy everyday-life YouTube Short. "
            "Read EXACTLY the complete Korean text below, from start to finish, in a lively, clear, natural voice. "
            "One consistent male narrator, no music, no extra words, no invented repetitions, preserve each paragraph boundary with a short breath. "
            "The only request to subscribe and like is in the very last sentence.\n\n"+script)
    res=client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",contents=prompt,
        config=types.GenerateContentConfig(response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
    candidates=getattr(res,"candidates",None) or []
    if not candidates or not candidates[0].content:raise RuntimeError("Gemini no speech candidate")
    parts=candidates[0].content.parts or []
    data=next((p.inline_data for p in parts if getattr(p,"inline_data",None) and p.inline_data.data),None)
    if not data:raise RuntimeError("Gemini TTS empty")
    raw=OUT/f"{key}_raw.wav"
    if data.data[:4]==b"RIFF":raw.write_bytes(data.data)
    else:
        m=re.search(r"rate=(\d+)",data.mime_type or "")
        with wave.open(str(raw),"wb") as h:
            h.setnchannels(1);h.setsampwidth(2);h.setframerate(int(m.group(1)) if m else 24000);h.writeframes(data.data)
    sped=OUT/f"{key}_gemini_charon_125.wav"
    ff("-i",raw,"-af","atempo=1.25","-ar","24000","-ac","1",sped)
    sec=wavduration(sped)
    if sec<30 or sec>100:raise RuntimeError(f"Unexpected TTS duration {sec}")
    (OUT/f"{key}_script.txt").write_text(script,encoding="utf-8")
    print("TTS",key,round(sec,2),"seconds","Gemini Charon",flush=True)
    return sped,sec
def split_chunks(s,maxchars=26):
    words=s.split()
    chunks=[];current=""
    for w in words:
        candidate=(current+" "+w).strip()
        if len(candidate)>maxchars and current:
            chunks.append(current);current=w
        else:current=candidate
    if current:chunks.append(current)
    if len(chunks)>=2 and len(chunks[-1])<7:chunks[-2]+=" "+chunks.pop()
    return chunks
def boundaries(audio_file,lines,duration):
    import numpy as np
    goals=np.cumsum([len(normalized(v))+1 for v in lines])[:-1]
    goals=goals/sum(len(normalized(v))+1 for v in lines)*duration
    with wave.open(str(audio_file),"rb") as h:
        sr=h.getframerate();sig=np.frombuffer(h.readframes(h.getnframes()),dtype=np.int16).astype("float32")
    hop=max(1,int(sr*.04));n=len(sig)//hop
    powers=np.sqrt(np.mean(sig[:n*hop].reshape(n,hop)**2,axis=1))
    pts=[0.]
    for goal in goals:
        lo=max(0,int((goal-.65)/.04));hi=min(n,int((goal+.65)/.04))
        if hi>lo:
            idx=np.arange(lo,hi)
            score=powers[lo:hi]+np.abs(idx*.04-goal)*max(1,np.percentile(powers,60))*.3
            best=float(idx[np.argmin(score)]*.04)
        else:best=float(goal)
        pts.append(max(pts[-1]+2.0,min(duration-2,best)))
    pts.append(duration)
    return pts
def render_slide(image_file,headline,caption,category):
    bg=Image.open(image_file).convert("RGB")
    bg=ImageOps.fit(bg,(W,H-256),method=Image.Resampling.LANCZOS,centering=(.5,.5))
    c=Image.new("RGB",(W,H),CREAM);c.paste(bg,(0,256))
    d=ImageDraw.Draw(c)
    d.rectangle((0,0,720,256),fill=CREAM)
    d.rounded_rectangle((20,19,249,71),radius=16,fill=NAVY)
    d.text((134,46),"생활알고리즘",font=f(28),fill=WHITE,anchor="mm")
    d.text((684,46),category,font=f(22),fill=NAVY,anchor="rm")
    d.text((360,130),headline[0],font=f(46),fill="#14263B",anchor="mm")
    d.text((360,194),headline[1],font=f(47),fill="#14263B",anchor="mm")
    d.rectangle((30,247,690,253),fill="#C69A42")
    # White heavy text with dark thick outlines over a lightly darkened translucent area.
    dark=Image.new("RGBA",(W,H),(0,0,0,0))
    over=ImageDraw.Draw(dark)
    over.rounded_rectangle((16,848,704,1064),radius=27,fill=(0,0,0,125))
    c=Image.alpha_composite(c.convert("RGBA"),dark)
    d=ImageDraw.Draw(c)
    lines=[];parts=caption.split();ln=""
    for word in parts:
        test=(ln+" "+word).strip()
        if d.textbbox((0,0),test,font=f(49))[2]<625:ln=test
        else:
            if ln:lines.append(ln)
            ln=word
    if ln:lines.append(ln)
    sz=49
    if len(lines)>2:
        sz=42;lines=[];ln=""
        for word in parts:
            test=(ln+" "+word).strip()
            if d.textbbox((0,0),test,font=f(sz))[2]<633:ln=test
            else:
                if ln:lines.append(ln)
                ln=word
        if ln:lines.append(ln)
    leading=sz+11
    y=951-(len(lines)-1)*leading/2
    for j,t in enumerate(lines):
        d.text((360,int(y+j*leading)),t,font=f(sz),anchor="mm",fill="#FFFFFF",stroke_fill="#070B14",stroke_width=4)
    return c.convert("RGB")
def stamp(sec):
    n=round(sec*1000);m,n=divmod(n,60000);s,ms=divmod(n,1000)
    return f"00:{m:02}:{s:02},{ms:03}"
def render(key,cfg):
    pics,credits=photos(key,cfg["photos"])
    voice,total=audio(key,cfg["lines"])
    cuts=boundaries(voice,cfg["lines"],total)
    frame_dir=OUT/(key+"_frames");frame_dir.mkdir(exist_ok=True)
    entries=[];srt=[];idx=0
    for scene,(line,start,end) in enumerate(zip(cfg["lines"],cuts[:-1],cuts[1:])):
        blocks=split_chunks(line,25)
        weights=[len(normalized(t))+2 for t in blocks]
        div=sum(weights);off=0.0
        for block,weight in zip(blocks,weights):
            sec=(end-start)*weight/div
            png=frame_dir/f"frame{idx:03}.png"
            render_slide(pics[scene],cfg["headline"],block,"생활 안전" if key=="powerstrip" else "난방 절약").save(png)
            entries.append((png,max(.15,sec)))
            srt.append((start+off,start+off+sec,block))
            off+=sec;idx+=1
    concat=OUT/(key+"_frames.ffconcat")
    contents=["ffconcat version 1.0"]
    for filename,d in entries:
        contents += ["file '"+str(filename.resolve())+"'","duration "+f"{d:.5f}"]
    contents.append("file '"+str(entries[-1][0].resolve())+"'")
    concat.write_text("\n".join(contents)+"\n",encoding="utf-8")
    output=OUT/cfg["filename"]
    ff("-safe","0","-f","concat","-i",concat,"-i",voice,"-fps_mode","vfr","-r","30",
       "-map","0:v:0","-map","1:a:0","-vf","scale=1080:1920:flags=lanczos","-c:v","libx264","-preset","veryfast",
       "-crf","23","-pix_fmt","yuv420p","-c:a","aac","-b:a","128k",
       "-t",f"{total:.3f}","-movflags","+faststart",output)
    (OUT/(key+"_captions.srt")).write_text("\n".join(
        f"{i+1}\n{stamp(a)} --> {stamp(b)}\n{txt}\n"
        for i,(a,b,txt) in enumerate(srt)),encoding="utf-8")
    (OUT/(key+"_sources.txt")).write_text("\n".join(cfg["urls"]+credits),encoding="utf-8")
    meta={"title":" ".join(cfg["headline"]),"video":output.name,"seconds":round(total,2),
          "narration":"Gemini 2.5 Flash TTS / Charon / 1.25x","layout":"white header, full-height photograph, large outlined captions over footage",
          "1080x1920_requested":True,"size":"1080x1920","shots":len(cfg["lines"]),
          "caption_chunks":len(srt),"subscribe_once":True,"upload_to_youtube":False}
    (OUT/(key+"_meta.json")).write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
    assert output.stat().st_size>300000
    print("REVIEW_MP4_READY",output,output.stat().st_size,round(total,2),flush=True)
for k,v in CFG.items():
    render(k,v)
print("BOTH_GEMINI_CHARON_SHORTS_DONE")
