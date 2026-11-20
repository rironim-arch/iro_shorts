#!/usr/bin/env python3
"""Gemini Kore exact per-line TTS for Deokgu short. Single female narrator; each line independently aligned."""
import json,os,re,subprocess,time,wave
from pathlib import Path
from google import genai
from google.genai import types

OUT=Path("deokgu_voice_output")
OUT.mkdir(exist_ok=True)
LINES=[
"30킬로미터 넘게 떨어진 곳에 맡겨진 진돗개 덕구가 사라졌습니다.",
"황색 진돗개 덕구는 오랫동안 할아버지와 함께 살았죠.",
"할아버지는 건강이 나빠져 옛집 근처에 있는 둘째 아들 아파트로 옮겼습니다.",
"덕구는 데려갈 수 없어 30킬로미터 넘게 떨어진 지인의 집에 맡겼습니다.",
"그런데 어느 날, 목줄이 풀린 덕구가 사라졌습니다.",
"얼마 뒤 옛집 이웃이 이상한 광경을 발견했습니다.",
"사람이 떠난 뒤 풀이 듬성듬성 자란 마당.",
"황색 진돗개 한 마리가 그곳을 계속 서성이고 있었습니다.",
"덕구였습니다.",
"30킬로미터가 넘는 거리를 돌아, 할아버지와 살던 옛집을 찾아온 겁니다.",
"이웃의 연락을 받은 할아버지는 덕구를 만나러 왔습니다.",
"서로를 알아본 둘은 반가워 어쩔 줄 몰랐습니다.",
"하지만 할아버지는 여전히 덕구와 함께 살 수 없었습니다.",
"결국 옛집 근처 이웃에게 간곡히 부탁해 덕구를 다시 맡겼습니다.",
"그리고 지금도 일주일에 한두 번씩 덕구를 만나러 옵니다.",
"함께 살 수 없어도, 두 친구의 인연은 계속되고 있습니다.",
"이 이야기가 재미있으셨다면 구독과 좋아요 부탁드립니다."
]
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
def exec_(args):subprocess.run(args,check=True)
def fmt(t):
 ms=round(t*1000);hh,ms=divmod(ms,3600000);mm,ms=divmod(ms,60000);ss,ms=divmod(ms,1000)
 return f"{hh:02d}:{mm:02d}:{ss:02d},{ms:03d}"
timeline=[];start=0.0
for i,line in enumerate(LINES):
 prompt=("한국어 감동 사연 영상입니다. 차분하고 따뜻한 한국어 여성 내레이션 성우 한 사람이 자연스럽고 또렷하게 읽어 주세요. "
 "오직 다음 한 문장만 정확하게 읽습니다. 생략, 의역, 앞뒤의 추가 문장, 감탄사, 음악, 효과음 모두 금지. "
 "첫 글자부터 마지막 글자까지 정확하게 발음하세요. 읽고 나서 말하지 마세요.\n\n"+line)
 data=None
 for attempt in range(6):
  try:
   r=client.models.generate_content(
      model="gemini-2.5-flash-preview-tts",contents=prompt,
      config=types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
         prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")))))
   for p in r.candidates[0].content.parts:
    v=getattr(p,"inline_data",None)
    if v is not None and getattr(v,"data",None):data=v;break
   if data is not None:break
  except Exception as e:print("RETRY",i+1,attempt+1,str(e)[:140],flush=True)
  time.sleep(2*(attempt+1))
 if data is None:raise RuntimeError(f"TTS failed scene {i+1}")
 raw=OUT/f"raw_{i:02d}.wav"
 if data.data[:4]==b"RIFF":raw.write_bytes(data.data)
 else:
  m=re.search(r"rate=(\d+)",data.mime_type or "")
  with wave.open(str(raw),"wb") as w:
   w.setnchannels(1);w.setsampwidth(2);w.setframerate(int(m.group(1)) if m else 24000);w.writeframes(data.data)
 seg=OUT/f"line_{i:02d}.wav"
 exec_(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(raw),"-af",
  "atempo=1.25,loudnorm=I=-18:TP=-2:LRA=11,adelay=90,apad=pad_dur=0.16","-ar","24000","-ac","1",str(seg)])
 with wave.open(str(seg),"rb") as w:d=w.getnframes()/w.getframerate()
 timeline.append({"i":i,"start":round(start,3),"end":round(start+d,3),
  "duration":round(d,3),"text":line})
 start+=d
 print("LINE",i+1,"DURATION",round(d,3),"TOTAL",round(start,3),flush=True)
 time.sleep(0.4)
(OUT/"concat.txt").write_text("\n".join(f"file 'line_{i:02d}.wav'" for i in range(len(LINES)))+"\n")
exec_(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(OUT/"concat.txt"),"-c:a","pcm_s16le",str(OUT/"full_kore_125.wav")])
exec_(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(OUT/"full_kore_125.wav"),"-b:a","128k",str(OUT/"full_kore_125.mp3")])
srt=[]
for i,s in enumerate(timeline,1):
 srt.extend([str(i),f"{fmt(s['start'])} --> {fmt(s['end'])}",s["text"],""])
(OUT/"deokgu_kore_125.srt").write_text("\n".join(srt),encoding="utf-8")
(OUT/"timing.json").write_text(json.dumps({"title":"덕구의 귀향","voice":"Gemini Kore","speed":1.25,
 "duration":round(start,3),"scenes":timeline},ensure_ascii=False,indent=2),encoding="utf-8")
print("DONE",round(start,3),flush=True)
