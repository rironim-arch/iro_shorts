#!/usr/bin/env python3
"""Generate exact sentence-aligned Kore speech for a new 2D emotional webtoon short."""
import json, os, re, wave, subprocess, time
from pathlib import Path
from google import genai
from google.genai import types

OUT=Path("mother_cup_kore_output"); OUT.mkdir(exist_ok=True)
LINES=[
"엄마는 딸에게 소리를 지르려다가 갑자기 입을 다물었습니다.",
"대체 무슨 일이 있었을까요?",
"어느 날, 어린 딸이 엄마가 아끼던 찻잔을 깨뜨렸습니다.",
"화가 머리끝까지 난 엄마는 딸을 크게 혼내려 했습니다.",
"그런데 그 순간, 딸의 작은 손이 떨리고 있었습니다.",
"엄마… 일부러 그런 거 아니야.",
"엄마는 잠시 아무 말도 하지 않았습니다.",
"부엌으로 가서 물 한 잔을 마시고 천천히 숨을 골랐습니다.",
"잠시 후 돌아온 엄마가 딸에게 물었습니다.",
"우리 딸, 다친 데는 없니?",
"그 말을 들은 딸은 참았던 울음을 터뜨렸습니다.",
"엄마는 딸의 눈물을 닦아주며 조용히 안아주었습니다.",
"깨진 찻잔은 다시 살 수 있지만, 화가 나서 내뱉은 말은 아이의 마음에 오래 남을 수 있습니다.",
"때로는 화를 내지 않고 잠시 멈추는 것만으로도 소중한 사람의 마음을 지킬 수 있습니다.",
"여러분은 화가 날 때 어떻게 하시나요?",
"공감하셨다면 구독과 좋아요 부탁드립니다."
]
# Images refer to one consistent 3x4 storyboard, row major 0..11.
PANELS=[0,0,1,3,4,5,6,7,8,8,9,10,11,11,11,11]
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
 prompt=("한국어 감성 웹툰 사연의 내레이션입니다. 온화한 여성 성우 한 명의 목소리로 자연스럽고 또렷하게 읽어주세요. "
         "오직 다음 대본 내용만 정확하게 읽습니다. 원고를 생략하거나 바꾸거나 덧붙이지 마세요. 배경음과 효과음 금지. "
         "긴 정적 없이 자연스러운 호흡으로, 문장 끝까지 발음해야 합니다. 여자아이 대사는 한 여성의 약한 목소리로 연기하세요.\n\n"+line)
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
full=OUT/"mother_cup_kore_125.wav"
exec_(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(con),
       "-acodec","pcm_s16le",str(full)])
exec_(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(full),"-b:a","128k",str(OUT/"mother_cup_kore_125.mp3")])
srt=[]
for i,s in enumerate(timeline,1):
 srt+= [str(i),f"{fmt(s['start'])} --> {fmt(s['end'])}",s["text"],""]
(OUT/"mother_cup_kore_125.srt").write_text("\n".join(srt),encoding="utf-8")
(OUT/"timing.json").write_text(json.dumps({"title":"엄마가 화를 참았던 10초","model":"gemini-2.5-flash-preview-tts",
                "voice":"Kore","speed":1.25,"duration":round(start,3),"scenes":timeline},ensure_ascii=False,indent=2),encoding="utf-8")
print("SUCCESS",start,flush=True)
