"""Produce two SINGLE-TAKE Charon voiceovers and Pexels real-motion footage.
Manual review only. No social posting or fake traffic.
"""
from pathlib import Path
import os, re, json, wave, subprocess, time, requests
from google import genai
from google.genai import types
from google.genai.errors import ClientError
import imageio_ffmpeg
ROOT=Path("november_two_shorts_assets");ROOT.mkdir(exist_ok=True)
FF=imageio_ffmpeg.get_ffmpeg_exe()
CONTENT={
  "frost":{
    "title":"차 앞유리 얼었을 때 뜨거운 물? 절대 금지!",
    "voice":[
      "아침에 차 앞유리가 꽁꽁 얼었다면, 뜨거운 물부터 붓지 마세요.",
      "갑작스러운 온도 차 때문에 유리에 금이 갈 수 있습니다.",
      "먼저 차량의 앞유리 성에 제거 기능을 켜세요.",
      "얼음이 녹기 시작하면 플라스틱 성에 제거 도구로 조심히 밀어냅니다.",
      "와이퍼가 얼어붙었다면 억지로 작동하지 마세요.",
      "다음 날을 위해 미리 앞유리 덮개를 씌워두는 것도 좋습니다.",
      "생활알고리즘. 유익했다면 구독과 좋아요!"
    ],
    "captions":[
      "뜨거운 물? 절대 안 됩니다!",
      "온도 충격 → 유리 균열 위험",
      "먼저 앞유리 성에 제거 기능 ON",
      "플라스틱 스크레이퍼로 살살",
      "얼어붙은 와이퍼 억지로 작동 금지",
      "예방은 앞유리 덮개",
      "생활알고리즘 | 구독 · 좋아요"
    ]
  },
  "humidifier":{
    "title":"겨울 가습기, 수돗물 그냥 넣어도 될까?",
    "voice":[
      "겨울철 가습기, 수돗물 그냥 넣어도 될까요?",
      "초음파 가습기는 물속 미네랄까지 공기 중으로 퍼뜨릴 수 있어요.",
      "미국 환경보호청은 미네랄이 적은 증류수를 권장합니다.",
      "그런데 물만 바꾸면 끝일까요? 아닙니다.",
      "매일 남은 물을 버리고 물통을 닦아 말린 뒤 새 물을 넣으세요.",
      "휴대용 가습기는 사흘마다 청소하고, 세척제는 충분히 헹궈야 합니다.",
      "실내 습도는 오십 퍼센트를 넘기지 마세요.",
      "제품 설명서도 확인하세요. 생활알고리즘. 구독과 좋아요!"
    ],
    "captions":[
      "가습기에 수돗물 넣어도 될까?",
      "초음파식은 미네랄도 공기 중으로",
      "EPA 권장: 미네랄 적은 증류수",
      "물만 바꾸면 끝? 아닙니다",
      "매일 남은 물 버리고 말리기",
      "사흘마다 청소, 세척제 충분히 헹굼",
      "실내 습도 50% 이하",
      "생활알고리즘 | 구독 · 좋아요"
    ]
  }
}
VIDEOS={
  "frost":[
    (855571,"windshield_scraping_close"),
    (35864048,"windshield_ice_detail"),
    (4232207,"windshield_snow_scraping"),
    (35864035,"car_windshield_winter")
  ],
  "humidifier":[
    (6941200,"humidifier_in_bedroom"),
    (6941383,"humidifier_with_user"),
    (7408649,"humidifier_closeup"),
    (6634584,"diffuser_mist_closeup")
  ]
}
def run(*a, timeout=180):
 subprocess.run([FF,"-y","-hide_banner","-loglevel","error",*map(str,a)],timeout=timeout,check=True)
def voice(name,items,client):
 full="\n".join(items["voice"])
 assert full.count("구독과 좋아요")==1, "One CTA only"
 path=ROOT/f"{name}_raw.wav"
 prompt=("Read the following Korean text as ONE continuous voiceover with a SINGLE consistently warm but credible male narrator voice. "
         "Speak ONLY the script, exactly in order. Do not add, remove, repeat, improvise, or prepend words. "
         "Do not insert any extra like/subscribe call except the very last line. "
         "Natural informative speech suitable for short-form science education. No music or sound effects.\n"
         "BEGIN TEXT\n"+full+"\nEND TEXT")
 for attempt in range(3):
  try:
   r=client.models.generate_content(
    model="gemini-2.5-flash-preview-tts",contents=prompt,
    config=types.GenerateContentConfig(
      response_modalities=["AUDIO"],
      speech_config=types.SpeechConfig(
         voice_config=types.VoiceConfig(
           prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
   raw=next(p.inline_data for p in r.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data)
   data=raw.data;mime=raw.mime_type or ""
   if data.startswith(b"RIFF"):path.write_bytes(data)
   else:
    match=re.search(r"rate=(\d+)",mime)
    sr=int(match.group(1)) if match else 24000
    with wave.open(str(path),"wb") as f:
     f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr);f.writeframes(data)
   break
  except Exception as e:
   if attempt==2:raise
   print("TTS_RETRY",name,str(e)[:160],flush=True);time.sleep(10*(attempt+1))
 fast=ROOT/f"{name}_charon_125.wav"
 run("-i",path,"-af","atempo=1.25","-ar","24000","-ac","1",fast)
 with wave.open(str(fast),"rb") as w:dur=w.getnframes()/w.getframerate()
 if not 20<dur<100:raise RuntimeError(f"Unexpected duration: {dur}")
 items["duration"]=dur
 (ROOT/f"{name}_manifest.json").write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding="utf-8")
 print("VOICE_READY",name,round(dur,3),flush=True)
def options(id):
 ret=[]
 for ratio in [(1280,720),(720,1280),(720,1366),(960,540),(540,960),(1080,1920),(1920,1080),(960,960),(720,480)]:
  for fps in (25,24,30,50,60):
   ret.append(f"https://videos.pexels.com/video-files/{id}/{id}-hd_{ratio[0]}_{ratio[1]}_{fps}fps.mp4")
 ret.append(f"https://www.pexels.com/download/video/{id}/")
 return ret
def fetch(id,name,topic,s):
 final=ROOT/f"{topic}_{name}.mp4"
 for u in options(id):
  try:
   h=s.head(u,allow_redirects=True,timeout=3.0)
   if h.status_code!=200:continue
   if not any(x in h.headers.get("content-type","") for x in ("video","octet-stream")):continue
   sz=int(h.headers.get("content-length","0"))
   if sz>60_000_000:continue
   print("FOUND",topic,name,u,sz,flush=True)
   t=ROOT/f"raw_{id}.mp4"; n=0
   with s.get(u,stream=True,timeout=(6,80)) as r:
    r.raise_for_status()
    with t.open("wb") as f:
     for chunk in r.iter_content(700000):
      if chunk:
       n+=len(chunk)
       if n>60_000_000:raise ValueError("Too large")
       f.write(chunk)
   run("-i",t,"-t","10","-vf","scale=1080:1080:force_original_aspect_ratio=increase,crop=1080:1080,fps=24,format=yuv420p","-an","-c:v","libx264","-crf","25","-preset","veryfast",final)
   t.unlink(missing_ok=True)
   print("CLIP_READY",topic,name,final.stat().st_size,flush=True)
   return True
  except Exception as e:
   (ROOT/f"raw_{id}.mp4").unlink(missing_ok=True)
 print("CLIP_NOT_FOUND",topic,name,flush=True)
 return False
def main():
 client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
 for n,v in CONTENT.items(): voice(n,v,client)
 s=requests.Session();s.headers["User-Agent"]="Mozilla/5.0 (Creative educational shorts)"
 status={}
 for topic,items in VIDEOS.items():
  for id,name in items: status[f"{topic}_{name}"]=fetch(id,name,topic,s)
 (ROOT/"status.json").write_text(json.dumps(status,indent=2))
 (ROOT/"sources.txt").write_text(
   "Vehicle windscreen advice: https://www.aaa.com/autorepair/articles/how-to-deice-your-cars-windshield\n"
   "Humidifier water and cleaning: https://www.epa.gov/indoor-air-quality-iaq/use-and-care-home-humidifiers\n"
   "Pexels Licensed Stock: https://www.pexels.com/license/\n"+
   "\n".join(f"{name}: https://www.pexels.com/video/{id}/" for clips in VIDEOS.values() for id,name in clips),
   encoding="utf-8")
 print("ALL_ASSETS_READY",flush=True)
if __name__=="__main__":main()
