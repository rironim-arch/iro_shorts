#!/usr/bin/env python3
"""Generate exact sentence-aligned Kore speech for a new 2D emotional webtoon short."""
import json, os, re, wave, subprocess, time
from pathlib import Path
from google import genai
from google.genai import types

OUT=Path("father_dawn_kore_output"); OUT.mkdir(exist_ok=True)
LINES=[
  "엄마 장례식에서 아버지는 끝내 눈물 한 방울 흘리지 않으셨습니다.",
  "평생 말수가 적고 무뚝뚝했던 아버지.",
  "조문객 앞에서도, 엄마를 보내는 순간에도 담담하셨습니다.",
  "솔직히 저는 그런 아버지가 원망스러웠습니다.",
  "평생 함께 산 엄마인데… 어쩜 저렇게 담담하실까.",
  "장례를 모두 마친 그날 밤, 저는 친정집에서 잠이 들었습니다.",
  "새벽 다섯 시쯤, 부엌에서 그릇 소리가 들려왔습니다.",
  "방문을 열자 아버지가 홀로 밥을 드시고 계셨습니다.",
  "저는 문 앞에 서서 뒷모습만 바라봤습니다.",
  "그런데 맞은편 빈자리에도 밥과 국, 수저가 놓여 있었습니다.",
  "평생 엄마가 앉으시던 자리였습니다.",
  "그때 아버지의 어깨가 조금씩 들썩이기 시작했습니다.",
  "얼굴은 보이지 않았지만, 아버지가 울고 계신 걸 알 수 있었습니다.",
  "저는 차마 다가가지 못하고 문가에서 함께 울었습니다.",
  "그제야 깨달았습니다. 아버지는 슬프지 않으셨던 게 아니었습니다.",
  "누구에게도 보여주지 않고, 혼자서 그 슬픔을 감당하고 계셨던 겁니다.",
  "그날 새벽, 저는 아버지의 뒷모습을 평생 잊지 못할 겁니다."
]
PANELS=[0,1,2,0,2,3,4,5,6,7,8,9,10,11,11,10,11]
assert len(LINES)==len(PANELS)
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
def exec_(args):
 subprocess.run(args,check=True)
def fmt(t):
 ms=round(t*1000)
 hh,ms=divmod(ms,3600000)
 mm,ms=divmod(ms,60000)
 ss,ms=divmod(ms,1000)
 return f"{hh:02d}:{mm:02d}:{ss:02d},{ms:03d}"
timeline=[];start=0.
for i,line in enumerate(LINES):
 prompt=("한국어 가족 드라마 웹툰 사연의 내레이션입니다. 감정은 차분하게 억누르다가 마지막에 조용히 먹먹해지는 연기로 읽어주세요. 온화한 여성 성우 한 명의 목소리로 자연스럽고 또렷하게 읽어주세요. "
         "오직 다음 대본 내용만 정확하게 읽습니다. 원고를 생략하거나 바꾸거나 덧붙이지 마세요. 배경음과 효과음 금지. "
         "긴 정적 없이 자연스러운 호흡으로, 문장 끝까지 발음해야 합니다. 여성 1인칭 독백만 연기하세요. 과장된 울음 연기나 대사 외 내용은 금지.\n\n"+line)
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
full=OUT/"father_dawn_kore_125.wav"
exec_(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(con),
       "-acodec","pcm_s16le",str(full)])
exec_(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(full),"-b:a","128k",str(OUT/"father_dawn_kore_125.mp3")])
srt=[]
for i,s in enumerate(timeline,1):
 srt+= [str(i),f"{fmt(s['start'])} --> {fmt(s['end'])}",s["text"],""]
(OUT/"father_dawn_kore_125.srt").write_text("\n".join(srt),encoding="utf-8")
(OUT/"timing.json").write_text(json.dumps({"title":"장례식에서 울지 않던 아버지","model":"gemini-2.5-flash-preview-tts",
                "voice":"Kore","speed":1.25,"duration":round(start,3),"scenes":timeline},ensure_ascii=False,indent=2),encoding="utf-8")
print("SUCCESS",start,flush=True)
