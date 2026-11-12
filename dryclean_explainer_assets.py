"""Produce Gemini Charon per-scene narration and licensed actual-motion stock cutouts.
Read-only source download, no YouTube upload.
"""
import os, re, json, wave, asyncio, time, subprocess, requests
from pathlib import Path
from google import genai
from google.genai import types
from google.genai.errors import ClientError
import imageio_ffmpeg

OUT=Path("dry_cleaning_assets");OUT.mkdir(exist_ok=True)
FF=imageio_ffmpeg.get_ffmpeg_exe()
LINES=[
("드라이클리닝, 옷을 물 없이 말린 채 닦는 걸까요?","드라이클리닝은 물 없이?"),
("사실 드라이클리닝도 액체로 세탁합니다. 물 대신 특수 세척 용제를 사용하죠.","물 대신 특수 용제로 세탁!"),
("세탁소에서는 먼저 옷의 소재와 얼룩을 확인하고, 필요한 곳은 미리 얼룩을 처리합니다.","첫째, 옷감·얼룩 확인"),
("전용 기계 안에서 옷과 용제가 함께 움직이면서 기름때와 피지를 제거합니다.","둘째, 용제로 기름때 제거"),
("세척 후에는 회전시켜 용제를 빼고, 건조 과정에서 용제를 회수해 다시 쓰기도 합니다.","셋째, 탈액 · 건조 · 용제 회수"),
("마지막에는 스팀과 프레스로 주름을 펴고 옷의 모양을 잡아 줍니다.","넷째, 스팀 · 프레스"),
("물세탁은 땀처럼 물에 녹는 때에, 드라이클리닝은 기름때에 상대적으로 유리합니다.","물세탁 vs 드라이클리닝"),
("어떤 방법이 맞을지는 옷의 세탁 표시를 확인하세요. 생활알고리즘! 구독과 좋아요!","세탁 표시 확인!  구독 · 좋아요"),
]
# Stock videos are real people and clothing in commercial laundries or steam ironing. NOT claimed to be specific dry-cleaning apparatus.
STOCK=[
(8756699,"commercial_laundry_workers","https://www.pexels.com/video/a-man-and-a-woman-working-in-a-laundry-facility-8756699/"),
(8756703,"laundry_worker","https://www.pexels.com/video/a-woman-working-in-a-laundry-facility-8756703/"),
(8756886,"garment_loading","https://www.pexels.com/video/woman-putting-clothes-in-washing-machine-8756886/"),
(8756891,"rotating_clothes","https://www.pexels.com/video/clothes-inside-the-washing-machine-8756891/"),
(10558374,"garment_steaming","https://www.pexels.com/video/close-up-shot-of-a-man-steaming-a-white-t-shirt-10558374/"),
(36302138,"tailor_steam_press","https://www.pexels.com/video/skilled-tailor-ironing-fabric-with-precision-36302138/"),
]
def ff(*args,timeout=100):
    return subprocess.run([FF,"-y","-hide_banner","-loglevel","error",*map(str,args)],check=True,timeout=timeout)
def tts(text,output):
    client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    r=client.models.generate_content(
      model="gemini-2.5-flash-preview-tts",
      contents=("읽을 내용 이외의 다른 말이나 인트로는 절대로 하지 마세요. 한국어 남성 성우 Charon으로 친근하지만 또렷하게, 짧은 교육 쇼츠처럼 자연스럽게 말하세요. 글자를 바꾸거나 생략하거나 구독과 좋아요를 덧붙이지 마세요. 오직 다음 문장만 읽으세요.\n\n"+text),
      config=types.GenerateContentConfig(response_modalities=["AUDIO"],
         speech_config=types.SpeechConfig(
           voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
    raw=next(p.inline_data for p in r.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data)
    data=raw.data
    if data.startswith(b"RIFF"):output.write_bytes(data)
    else:
       mime=(raw.mime_type or "").lower()
       rate=int(re.search(r"rate=(\d+)",mime).group(1)) if re.search(r"rate=(\d+)",mime) else 24000
       with wave.open(str(output),"wb") as w:
          w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(data)
    with wave.open(str(output),"rb") as w: dur=w.getnframes()/w.getframerate()
    if dur<1:raise RuntimeError("Empty voice response")
    return dur
def fetch_video(id):
   dest=OUT/f"raw_{id}.mp4"
   options=[f"https://www.pexels.com/video/download/{id}/"]
   for size in ("720_1280","1280_720","960_540","540_960","1920_1080","1080_1920"):
      for fps in (25,30,24,50,60):
         options.append(f"https://videos.pexels.com/video-files/{id}/{id}-hd_{size}_{fps}fps.mp4")
   session=requests.Session();session.headers["User-Agent"]="Mozilla/5.0 (Shorts Editorial Production)"
   for url in options:
      try:
         if url != options[0]:
            h=session.head(url,timeout=4,allow_redirects=True)
            if h.status_code!=200 or "video" not in h.headers.get("content-type",""):continue
            if int(h.headers.get("content-length","0"))>65_000_000:continue
         with session.get(url,stream=True,timeout=(7,45)) as r:
            r.raise_for_status()
            if not any(x in r.headers.get("content-type","") for x in ("video","octet-stream")):continue
            n=0
            with dest.open("wb") as w:
               for b in r.iter_content(524288):
                  if b:
                     n+=len(b)
                     if n>65_000_000:raise RuntimeError("Large file")
                     w.write(b)
         if dest.stat().st_size>100000:
            ff("-i",dest,"-frames:v","1","-f","null","-",timeout=25)
            return dest
      except Exception:dest.unlink(missing_ok=True)
   return None
async def main():
   manifest=[]
   for i,(line,caption) in enumerate(LINES):
      path=OUT/f"scene_{i:02d}_raw.wav"
      for attempt in range(3):
         try:
           dur=await asyncio.to_thread(tts,line,path)
           break
         except ClientError as e:
           if attempt==2:raise
           print("TTS_RATE_LIMIT",str(e)[:150],flush=True)
           await asyncio.sleep(24)
      sped=OUT/f"scene_{i:02d}_125.wav"
      ff("-i",path,"-filter:a","atempo=1.25","-ar","24000","-ac","1",sped)
      with wave.open(str(sped),"rb") as w:
         secs=w.getnframes()/w.getframerate()
      manifest.append({"index":i,"narration":line,"caption":caption,"voice":sped.name,"duration":round(secs,4)})
      print("VOICE",i,secs,flush=True)
      await asyncio.sleep(1.5)
   (OUT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
   for id,name,url in STOCK:
       f=fetch_video(id)
       if f is None:
          print("NO_VIDEO",id,flush=True);continue
       result=OUT/f"clip_{name}.mp4"
       try:
         ff("-ss","0.5","-i",f,"-t","8","-vf","scale=960:960:force_original_aspect_ratio=increase,crop=960:960,fps=15,format=yuv420p",
            "-an","-c:v","libx264","-crf","27","-preset","veryfast","-movflags","+faststart",result,timeout=130)
         print("CLIP",name,result.stat().st_size,flush=True)
       except Exception as e:
         print("ENCODE_ERROR",name,str(e)[:180],flush=True)
       f.unlink(missing_ok=True)
   (OUT/"sources.txt").write_text(
       "Narration facts: https://dlionline.org/cleaning-processes-clothing-care/\n"
       "https://www.drycleanersweb.com.au/consumers/what-is-drycleaning/\n"
       "Stock illustrates laundry work and garment handling, NOT proof of proprietary dry-cleaning chemical machinery.\n"
       "Pexels License: https://www.pexels.com/license/\n"
       + "\n".join(f"{name}: {url}" for _,name,url in STOCK),encoding="utf-8")
   print("ASSETS_COMPLETE",flush=True)
if __name__=="__main__":asyncio.run(main())
