"""One continuous Gemini Charon TTS take + public Pexels moving footage for AlphaGo short v2.
Only source clips and original audio; no social media uploads.
"""
from pathlib import Path
import subprocess, json, wave, os, re, requests
from google import genai
from google.genai import types
import imageio_ffmpeg
OUT=Path("alphago_v2_assets");OUT.mkdir(exist_ok=True)
FF=imageio_ffmpeg.get_ffmpeg_exe()
NARRATION=[
"2016년, 알파고가 이세돌 9단을 4대 1로 이겼습니다.",
"하지만 당시 알파고는 바둑에 특화된 천재였어요. 사람과 자유롭게 대화하거나 글을 쓰지는 못했죠.",
"10년이 지난 2026년. 지금의 인공지능은 글을 쓰고, 사진과 음성을 이해하며, 프로그램 코드까지 만듭니다.",
"복잡한 문서를 분석하고, 컴퓨터에서 여러 단계의 작업을 돕는 인공지능도 등장했습니다.",
"놀라운 성과도 있었죠. 2025년, 구글의 제미나이 딥 씽크는 국제수학올림피아드에서 42점 만점에 35점, 금메달 수준을 기록했습니다.",
"그렇다면 인공지능이 인간보다 모든 분야에서 똑똑할까요? 꼭 그렇지는 않습니다.",
"스탠퍼드의 2026년 인공지능 지수에 따르면, 최고 수준 모델도 아날로그 시계 읽기 정답률이 약 50퍼센트였습니다.",
"컴퓨터를 직접 조작하는 평가에서도 성공률은 약 66퍼센트였습니다. 아직 실수할 때가 많다는 거죠.",
"알파고가 한 분야의 전문가였다면, 지금의 인공지능은 다양한 분야의 조력자입니다.",
"하지만 잘못된 정보를 자신 있게 말할 수도 있으니 중요한 답은 검증해야 합니다.",
"여러분은 앞으로 10년 뒤, 인공지능이 얼마나 더 발전할 거라고 생각하나요? 생활알고리즘. 구독과 좋아요!"
]
VIDEO_IDS=[
 (5495890,"coding_vertical"),
 (5925283,"coding_hands"),
 (5474318,"coding_screen"),
 (9160922,"clock_real"),
 (7033786,"clock_ticking"),
 (32386519,"robot_arm"),
 (8275951,"coding_office"),
 (6330778,"coding_silhouette"),
]
def ff(*args,timeout=130):
 subprocess.run([FF,"-y","-hide_banner","-loglevel","error",*map(str,args)],check=True,timeout=timeout)
def make_voice():
 client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
 transcript="\n".join(NARRATION)
 r=client.models.generate_content(
   model="gemini-2.5-flash-preview-tts",
   contents=("Audio task: Korean voiceover narration. Use one consistent single male announcer voice, natural warm clear informative Korean, same vocal pitch throughout. Read EXACTLY the script below. Do NOT add any words before or after it. Do not repeat lines. Do not add a call-to-action except the words explicitly in the script. No music or introductions.\n\nSCRIPT START\n"+transcript+"\nSCRIPT END"),
   config=types.GenerateContentConfig(
     response_modalities=["AUDIO"],
     speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
       prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
 inline=next(p.inline_data for p in r.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data)
 raw=inline.data; dest=OUT/"full_charon_original.wav"
 if raw[:4]==b"RIFF":dest.write_bytes(raw)
 else:
   rate=int(re.search(r"rate=(\d+)",inline.mime_type or "").group(1)) if re.search(r"rate=(\d+)",inline.mime_type or "") else 24000
   with wave.open(str(dest),"wb") as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes(raw)
 with wave.open(str(dest),"rb") as f:seconds=f.getnframes()/f.getframerate()
 print("FULL_TAKE_SECONDS",seconds,flush=True)
 if seconds<45:raise RuntimeError("Suspiciously short full narration: "+str(seconds))
 fast=OUT/"full_charon_125.wav"
 ff("-i",dest,"-af","atempo=1.25","-ac","1","-ar","24000",fast)
 with wave.open(str(fast),"rb") as f:fast_seconds=f.getnframes()/f.getframerate()
 print("SPEEDED_FULL_TAKE_SECONDS",fast_seconds,flush=True)
 (OUT/"transcript.json").write_text(json.dumps({"lines":NARRATION,"original_duration":seconds,"duration":fast_seconds,"voice":"Gemini 2.5 Flash TTS Charon","speed":1.25},ensure_ascii=False,indent=2))
def clips():
 session=requests.Session();session.headers["User-Agent"]="Mozilla/5.0"
 for id,name in VIDEO_IDS:
  dest=OUT/f"clip_{name}.mp4"
  urls=[f"https://www.pexels.com/download/video/{id}/"]
  for wh in ("720_1280","1280_720","1080_1920","1920_1080","720_1366","960_540","540_960","1280_800","720_480"):
   for fr in (25,30,24,60):
     urls.insert(0,f"https://videos.pexels.com/video-files/{id}/{id}-hd_{wh}_{fr}fps.mp4")
  urls=list(dict.fromkeys(urls))
  found=False
  for url in urls:
   try:
    head=session.head(url,timeout=2.5,allow_redirects=True)
    if head.status_code!=200:continue
    n=int(head.headers.get("content-length","0"))
    if n>55_000_000:continue
    if ("video" not in head.headers.get("content-type","") and "octet" not in head.headers.get("content-type","")):continue
    print("FETCHING",name,url,n,flush=True)
    original=OUT/f"raw_{id}.mp4"
    with session.get(url,timeout=(5,60),stream=True) as r:
       r.raise_for_status()
       size=0
       with original.open("wb") as file:
         for b in r.iter_content(500000):
            if b:
              size+=len(b)
              if size>55_000_000:raise RuntimeError("Too big")
              file.write(b)
    ff("-i",original,"-t","9","-vf","scale=900:900:force_original_aspect_ratio=increase,crop=900:900,fps=24,format=yuv420p",
       "-an","-c:v","libx264","-crf","25","-preset","veryfast",dest)
    original.unlink(missing_ok=True)
    print("CLIP_READY",name,dest.stat().st_size,flush=True)
    found=True
    break
   except Exception as e:
    original=OUT/f"raw_{id}.mp4";original.unlink(missing_ok=True)
  if not found:print("CLIP_UNAVAILABLE",name,flush=True)
 (OUT/"sources.txt").write_text("Pexels license: https://www.pexels.com/license/\n"+
 "\n".join(f"{name}: https://www.pexels.com/video/{id}/" for id,name in VIDEO_IDS))
if __name__=="__main__":
 make_voice()
 clips()
