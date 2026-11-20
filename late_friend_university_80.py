#!/usr/bin/env python3
"""80-second Gemini Kore one-voice narration — university friends, habits story."""
import json,os,re,subprocess,wave,time
from pathlib import Path
from google import genai
from google.genai import types
import imageio_ffmpeg
OUT=Path("late_friend_80_voice_output");OUT.mkdir(exist_ok=True)
LINES=[
"그 친구는 정말 좋은 사람이었습니다.",
"대학교 때부터 함께한 친구는 마음씨 좋고 의리도 있었죠.",
"제가 힘들 때면 누구보다 먼저 달려와 주는 친구였습니다.",
"그런데 약속 시간만큼은 늘 늦었습니다.",
"10분은 기본, 심할 땐 30분씩 기다렸죠.",
"야, 제발 좀 일찍 와. 약속은 지켜야지.",
"알았어, 다음엔 안 늦을게.",
"우리는 대학교를 졸업하고 사회생활을 시작했습니다.",
"하지만 친구의 지각 버릇은 여전했죠.",
"너 그러다 정말 중요한 날에도 늦으면 어떡해?",
"에이, 중요한 날엔 절대 안 늦어!",
"그러던 어느 날, 친구에게 기다리던 이직 기회가 찾아왔습니다.",
"몇 달 동안 준비한 회사의 최종 면접이었죠.",
"이번에는 꼭 일찍 출발해.",
"하지만 면접 당일, 친구는 평소처럼 늦게 집을 나섰습니다.",
"길까지 막혀 면접장에 도착하니 이미 입실 시간이 지났습니다.",
"아무리 사정해도 면접장에 들어갈 수 없었죠.",
"그날 저녁, 친구에게 전화가 왔습니다.",
"늘 밝던 친구가 울먹였습니다.",
"네가 시간 지키라고 했는데… 왜 그 말을 안 들었을까?",
"친구가 잃은 건 몇 분이 아니라, 오랫동안 준비한 기회였습니다.",
"습관이 무서운 이유는, 반복되면 잘못된 행동도 당연해진다는 겁니다.",
"그리고 그 대가는 때로 인생에서 가장 중요한 순간에 찾아옵니다.",
"이 이야기가 마음에 남으셨다면 구독과 좋아요 부탁드립니다."
]
full="\n".join(LINES)
assert len(LINES)==24
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
ff=imageio_ffmpeg.get_ffmpeg_exe()
def run(args):subprocess.run(args,check=True)
def getaudio(text):
 prompt=("한국어 인생 사연 숏츠의 **여성 성우 한 명**이 읽는 전체 대사입니다. "
 "차분하고 자연스러운 따뜻한 여성 목소리로, 시작부터 끝까지 같은 음색과 말하는 속도를 유지하세요. "
 "별도의 효과음, 음악, 자기소개는 없으며 아래 내용만 정확하게 발음하세요. 단어 누락, 건너뜀, 추가 대사 절대 금지. "
 "마지막 문장 '구독과 좋아요 부탁드립니다'까지 반드시 완독해 주세요. "
 "친구의 직접 대사 부분도 동일 성우의 감정 톤으로 읽으세요.\n\n"+text)
 r=client.models.generate_content(model="gemini-2.5-flash-preview-tts",contents=prompt,
  config=types.GenerateContentConfig(response_modalities=["AUDIO"],
  speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
  prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")))))
 for p in r.candidates[0].content.parts:
  d=getattr(p,"inline_data",None)
  if d is not None and getattr(d,"data",None):return d
 raise ValueError("Gemini returned no inline audio")
for attempt in range(3):
 try:
  blob=getaudio(full)
  raw=OUT/"full_raw.wav"
  if blob.data[:4]==b"RIFF":raw.write_bytes(blob.data)
  else:
   m=re.search(r"rate=(\d+)",blob.mime_type or "")
   with wave.open(str(raw),"wb") as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(int(m.group(1)) if m else 24000);w.writeframes(blob.data)
  run([ff,"-loglevel","error","-y","-i",str(raw),"-af",
       "atempo=1.25,loudnorm=I=-18:TP=-2:LRA=9,adelay=120,apad=pad_dur=0.25",
       "-ac","1","-ar","24000","-sample_fmt","s16",str(OUT/"kore_125.wav")])
  with wave.open(str(OUT/"kore_125.wav"),"rb") as w:
   duration=w.getnframes()/w.getframerate()
  print("TAKE",attempt,"DURATION",duration,flush=True)
  if duration<57:raise ValueError("Audio truncated; duration "+str(duration))
  run([ff,"-loglevel","error","-y","-i",str(OUT/"kore_125.wav"),"-b:a","160k",str(OUT/"kore_125.mp3")])
  (OUT/"timing.json").write_text(json.dumps({"title":"늘 늦던 내 친구 — 습관이 부른 후회","voice":"Gemini Kore","speed":1.25,
   "duration":round(duration,4),"text":full,"lines":LINES,"one_take":True},ensure_ascii=False,indent=2),encoding="utf-8")
  print("SUCCESS",duration,flush=True)
  break
 except Exception as e:
  print("ERROR",attempt,str(e)[:500],flush=True)
  if attempt==2:raise
  time.sleep(3*(attempt+1))
