#!/usr/bin/env python3
"""Generate exact sentence-aligned Kore speech for a new 2D emotional webtoon short."""
import json, os, re, wave, subprocess, time
from pathlib import Path
from google import genai
from google.genai import types

OUT=Path("baekgu_kore_output"); OUT.mkdir(exist_ok=True)
LINES=[
 "300킬로미터를 넘어 돌아온 하얀 진돗개. 도대체 누구를 찾아온 걸까요?",
 "1993년, 진도에는 박복단 할머니와 백구가 살았습니다.",
 "그해 3월, 백구는 대전으로 팔려갔습니다.",
 "어느 날, 백구는 새로운 집에서 빠져나왔습니다.",
 "그 여정은 정확히 알려지지 않았습니다.",
 "일곱 달 뒤, 백구는 진도의 옛집에 나타났습니다.",
 "뼈와 가죽만 남을 만큼 야윈 모습이었습니다.",
 "백구를 다시 본 할머니는 얼마나 놀랐을까요.",
 "무려 300킬로미터가 넘는 거리를 돌아온 겁니다.",
 "1996년에는 세진컴퓨터랜드 광고 모델이 됐습니다.",
 "백구의 변치 않는 마음은 평생 애프터서비스의 상징이 됐죠.",
 "사람들이 오래 기억한 건, 결국 집으로 돌아온 백구의 마음이었습니다.",
 "여러분은 이 마음을 뭐라 부르겠어요? 구독과 좋아요 부탁드립니다."
]
PANELS=[
 0,
 2,
 2,
 3,
 5,
 8,
 0,
 1,
 9,
 10,
 10,
 11,
 11
]
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
 prompt=("실제 1993년 진돗개 백구의 귀향을 다룬 한국어 감동 실화 웹툰의 내레이션입니다. 온화한 여성 성우 한 명의 목소리로 자연스럽고 또렷하게 읽어주세요. "
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
full=OUT/"baekgu_kore_125.wav"
exec_(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(con),
       "-acodec","pcm_s16le",str(full)])
exec_(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(full),"-b:a","128k",str(OUT/"baekgu_kore_125.mp3")])
srt=[]
for i,s in enumerate(timeline,1):
 srt+= [str(i),f"{fmt(s['start'])} --> {fmt(s['end'])}",s["text"],""]
(OUT/"baekgu_kore_125.srt").write_text("\n".join(srt),encoding="utf-8")
(OUT/"timing.json").write_text(json.dumps({"title":"300km를 돌아온 진돗개 백구","model":"gemini-2.5-flash-preview-tts",
                "voice":"Kore","speed":1.25,"duration":round(start,3),"scenes":timeline},ensure_ascii=False,indent=2),encoding="utf-8")
print("SUCCESS",start,flush=True)
