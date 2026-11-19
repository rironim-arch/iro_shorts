#!/usr/bin/env python3
"""Generate exact sentence-aligned Kore speech for a new 2D emotional webtoon short."""
import json, os, re, wave, subprocess, time
from pathlib import Path
from google import genai
from google.genai import types

OUT=Path("mother_photo_kore_output"); OUT.mkdir(exist_ok=True)
LINES=[
  "30년 치 가족사진에, 엄마 얼굴만 없었습니다.",
  "엄마 칠순잔치에 쓸 사진을 고르다가 그 사실을 알았습니다.",
  "입학식에도, 운동회에도, 가족여행에도.",
  "사진마다 아빠와 우리 남매만 환하게 웃고 있었습니다.",
  "저는 괜히 마음이 서운해져 사진첩을 한참 뒤적였습니다.",
  "그러다 문득 어릴 적 제가 자주 하던 말이 떠올랐습니다.",
  "엄마! 여기 봐! 우리 사진 찍어줘!",
  "엄마는 늘 웃으며 카메라를 들어주셨습니다.",
  "그날 밤, 구석에 놓인 낡은 캠코더를 발견했습니다.",
  "영상을 켜자 어린 저와 동생이 뛰어놀고 있었습니다.",
  "동생이 넘어져 울자, 카메라가 갑자기 흔들렸습니다.",
  "엄마가 촬영을 멈추고 달려가 동생을 품에 안았습니다.",
  "그러다 유리창에, 젊은 엄마의 얼굴이 잠깐 비쳤습니다.",
  "엄마는 우리를 바라보며 정말 행복하게 웃고 있었습니다.",
  "그제야 깨달았습니다. 엄마는 가족사진에서 빠진 사람이 아니었습니다.",
  "우리의 모든 순간을 기록해 주던 사람이었습니다.",
  "칠순잔치 날, 저는 엄마를 가족 한가운데 앉혔습니다.",
  "엄마, 오늘은 우리가 엄마 사진 찍어줄게.",
  "엄마는 쑥스러운 듯 웃으며 우리 손을 꼭 잡으셨습니다.",
  "그 사진은 지금, 우리 집에서 가장 잘 보이는 곳에 걸려 있습니다.",
  "공감하셨다면 구독과 좋아요 부탁드립니다."
]
PANELS=[0,0,1,2,3,3,5,6,3,6,7,7,8,8,8,8,9,10,11,11,11]
assert len(LINES)==len(PANELS)
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
def exec_(args):
 import shutil
 if args and args[0]=='ffmpeg' and not shutil.which('ffmpeg'):
  import imageio_ffmpeg
  args=[imageio_ffmpeg.get_ffmpeg_exe(),*args[1:]]
 subprocess.run(args,check=True)
def fmt(t):
 ms=round(t*1000)
 hh,ms=divmod(ms,3600000)
 mm,ms=divmod(ms,60000)
 ss,ms=divmod(ms,1000)
 return f"{hh:02d}:{mm:02d}:{ss:02d},{ms:03d}"
timeline=[];start=0.
for i,line in enumerate(LINES):
 prompt=("한국어 가족 드라마 웹툰 사연의 내레이션입니다. 처음에는 의아함을 담고, 중반에는 작은 발견의 놀라움을, 후반에는 따뜻한 감동을 담아 읽어주세요. 온화한 여성 성우 한 명의 목소리로 자연스럽고 또렷하게 읽어주세요. "
         "오직 다음 대본 내용만 정확하게 읽습니다. 원고를 생략하거나 바꾸거나 덧붙이지 마세요. 배경음과 효과음 금지. "
         "긴 정적 없이 자연스러운 호흡으로, 문장 끝까지 발음해야 합니다. 여성 1인칭 독백과 짧은 대사를 한 목소리로만 연기하세요. 과장된 울음 연기나 대사 외 내용은 금지.\n\n"+line)
 data=None
 for attempt in range(5):
  try:
   r=client.models.generate_content(model="gemini-2.5-flash-preview-tts", contents=prompt,
       config=types.GenerateContentConfig(response_modalities=["AUDIO"],speech_config=types.SpeechConfig(
           voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")))))
   for part in r.candidates[0].content.parts:
    v=getattr(part,"inline_data",None)
    if v is not None and getattr(v,"data",None):
     data=v;break
   if data is not None: break
  except Exception as e:
   print("retry",i,attempt,str(e)[:160],flush=True)
  time.sleep(4*(attempt+1))
 if data is None: raise RuntimeError(f"KORE_GENERATION_FAILED_{i}")
 raw=OUT/f"raw_{i:02d}.wav"
 if data.data[:4]==b"RIFF":raw.write_bytes(data.data)
 else:
  rate_match=re.search(r"rate=(\d+)",data.mime_type or "")
  with wave.open(str(raw),"wb") as w:
   w.setnchannels(1);w.setsampwidth(2)
   w.setframerate(int(rate_match.group(1)) if rate_match else 24000)
   w.writeframes(data.data)
 audio=OUT/f"segment_{i:02d}.wav"
 # protect first syllable and final syllable with a quarter second of silence on each side.
 exec_(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(raw),
         "-af","atempo=1.25,loudnorm=I=-18:TP=-2:LRA=11,adelay=120,apad=pad_dur=0.18",
         "-ar","24000","-ac","1",str(audio)])
 with wave.open(str(audio),"rb") as w:
  d=w.getnframes()/w.getframerate()
 timeline.append({"i":i,"start":round(start,3),"end":round(start+d,3),
                 "duration":round(d,3),"text":line,"panel":PANELS[i]})
 start+=d
 print("SCENE",i+1,"DURATION",round(d,3),"TOTAL",round(start,3),flush=True)
 time.sleep(0.5)
con=OUT/"concat.txt"
con.write_text("\n".join(f"file 'segment_{i:02d}.wav'" for i in range(len(LINES)))+"\n")
full=OUT/"mother_photo_kore_125.wav"
exec_(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(con),
       "-acodec","pcm_s16le",str(full)])
exec_(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(full),"-b:a","128k",str(OUT/"mother_photo_kore_125.mp3")])
srt=[]
for i,s in enumerate(timeline,1):
 srt+= [str(i),f"{fmt(s['start'])} --> {fmt(s['end'])}",s["text"],""]
(OUT/"mother_photo_kore_125.srt").write_text("\n".join(srt),encoding="utf-8")
(OUT/"timing.json").write_text(json.dumps({"title":"가족사진에 엄마만 없었던 이유","model":"gemini-2.5-flash-preview-tts",
                "voice":"Kore","speed":1.25,"duration":round(start,3),"scenes":timeline},ensure_ascii=False,indent=2),encoding="utf-8")
print("SUCCESS",start,flush=True)
