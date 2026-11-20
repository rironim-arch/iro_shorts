#!/usr/bin/env python3
"""Kore voice with consistent tone: 4 long contiguous takes rather than individual lines."""
import os,json,subprocess,re,wave,time
from pathlib import Path
from google import genai
from google.genai import types
OUT=Path("late_friend_kore_output");OUT.mkdir(exist_ok=True)
LINES=[
"그 친구는 정말 좋은 사람이었습니다.",
"고등학교 때부터 함께한 제 친구는 마음씨도 좋고 의리도 있었습니다.",
"제가 힘들 때면 누구보다 먼저 달려와 주는 친구였죠.",
"하지만 딱 하나, 고치지 못하는 버릇이 있었습니다.",
"바로 약속 시간에 항상 늦는 것이었습니다.",
"10분은 기본이고, 심할 때는 30분씩 기다려야 했습니다.",
"저는 그때마다 말했습니다.",
"야, 제발 약속 시간 좀 지켜. 조금만 일찍 나오면 되잖아.",
"그러면 친구는 늘 웃으며 대답했죠.",
"알았어, 알았어. 다음에는 안 늦을게.",
"그렇게 우리는 고등학교를 졸업하고 사회생활을 시작했습니다.",
"하지만 친구의 늦는 버릇은 여전했습니다.",
"너 그러다가 정말 중요한 약속에도 늦으면 어떡하려고 그래?",
"친구는 대수롭지 않게 말했습니다.",
"에이, 중요한 날에는 안 늦지. 걱정 마!",
"그러던 어느 날, 친구에게 정말 좋은 이직 기회가 찾아왔습니다.",
"몇 달 동안 준비했던 회사의 최종 면접이었습니다.",
"저는 다시 한번 당부했습니다.",
"이번만큼은 꼭 일찍 출발해.",
"그런데 면접 당일.",
"친구는 또 평소처럼 늦게 집을 나섰습니다.",
"설상가상으로 길까지 막혔고, 면접장에 도착했을 때는 이미 입실 시간이 지나 있었습니다.",
"친구는 사정했지만 결국 면접에 들어갈 수 없었습니다.",
"그날 저녁, 친구에게 전화가 왔습니다.",
"평소 밝기만 하던 친구가 울먹이며 말했습니다.",
"네가 그렇게 시간 지키라고 했는데… 내가 왜 그 말을 안 들었을까.",
"저는 아무 말도 할 수 없었습니다.",
"친구가 잃어버린 건 단순히 몇 분이 아니라, 오랫동안 준비했던 소중한 기회였으니까요.",
"습관이 무서운 이유는, 잘못된 행동조차 반복되면 너무 익숙해져 잘못인지 느끼지 못하게 만든다는 겁니다.",
"그리고 그 대가는 때로 인생에서 가장 중요한 순간에 찾아옵니다.",
"이 이야기가 마음에 남으셨다면 구독과 좋아요 부탁드립니다."
]
CUTS=[0,8,15,23,31]
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
def run(cmd):subprocess.run(cmd,check=True)
times=[];elapsed=0.
for ci in range(len(CUTS)-1):
 lo,hi=CUTS[ci:ci+2]
 text="\n".join(LINES[lo:hi])
 prompt=("한국어 인생 사연 한 편을 읽고 있는 동일한 여성 성우입니다. "
  "모든 문장을 같은 차분하고 따뜻한 톤, 자연스러운 속도와 억양으로 한 번에 이어 읽으세요. "
  "드라마틱하게 목소리를 크게 바꾸거나 높이지 마세요. 설명, 추가 대사, 효과음, 배경음악 없이 원문만 정확히 낭독하세요. "
  "문장과 문장 사이는 짧게 한 호흡 쉬고, 한 글자도 빠뜨리거나 덧붙이지 마세요. 말끝까지 또렷하게 읽으세요.\n\n"+text)
 data=None
 for attempt in range(5):
  try:
   response=client.models.generate_content(model="gemini-2.5-flash-preview-tts",contents=prompt,
     config=types.GenerateContentConfig(response_modalities=["AUDIO"],
       speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
       prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")))))
   for part in response.candidates[0].content.parts:
    d=getattr(part,"inline_data",None)
    if d is not None and getattr(d,"data",None):data=d;break
   if data:break
  except Exception as exc:print("retry",ci,attempt,str(exc)[:150],flush=True)
  time.sleep(2+attempt*3)
 if data is None:raise RuntimeError(f"Missing audio for chunk {ci}")
 raw=OUT/f"chunk_{ci:02d}_raw.wav"
 if data.data[:4]==b"RIFF": raw.write_bytes(data.data)
 else:
  match=re.search(r"rate=(\d+)",data.mime_type or "")
  with wave.open(str(raw),"wb") as f:
   f.setnchannels(1);f.setsampwidth(2);f.setframerate(int(match.group(1)) if match else 24000);f.writeframes(data.data)
 target=OUT/f"chunk_{ci:02d}_125.wav"
 run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(raw),
      "-af","atempo=1.25,loudnorm=I=-17:TP=-2:LRA=8,adelay=90,apad=pad_dur=0.14",
      "-ar","24000","-ac","1","-sample_fmt","s16",str(target)])
 with wave.open(str(target),"rb") as f:d=f.getnframes()/f.getframerate()
 times.append(dict(chunk=ci,start=round(elapsed,3),end=round(elapsed+d,3),
  duration=round(d,3),line_start=lo,line_end=hi,lines=LINES[lo:hi]))
 elapsed+=d
 print(f"CHUNK {ci+1}/{len(CUTS)-1}: {d:.2f}s cumulative {elapsed:.2f}s, chars {len(text)}",flush=True)
 time.sleep(.5)
(OUT/"concat.txt").write_text("\n".join("file 'chunk_%02d_125.wav'"%i for i in range(len(times)))+"\n",encoding="utf-8")
full=OUT/"late_friend_kore_125.wav"
run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(OUT/"concat.txt"),"-c:a","pcm_s16le",str(full)])
run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(full),"-b:a","160k",str(OUT/"late_friend_kore_125.mp3")])
(OUT/"timing.json").write_text(json.dumps(dict(title="습관이 무서운 이유",voice="Gemini Kore",
 speed=1.25,approach="four continuous clips of same voice",duration=round(elapsed,3),lines=LINES,
 chunks=times),ensure_ascii=False,indent=2),encoding="utf-8")
print("SUCCESS voice duration",round(elapsed,3),flush=True)
