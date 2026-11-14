"""Produce one continuous Korean Gemini Charon TTS take, for a fictional mini webtoon."""
import os, wave, re, time, json
from pathlib import Path
from google import genai
from google.genai import types
import subprocess, imageio_ffmpeg
d=Path("psych_story_audio");d.mkdir(exist_ok=True)
lines=[
"3년 동안 저를 무시하던 직장 동료가 있었습니다.",
"인사를 해도 못 들은 척. 회의에서는 제 말을 끊었죠.",
"그런데 어느 날, 그 사람이 웃으며 커피를 건넸습니다.",
"어제까지 눈도 마주치지 않던 사람이 말입니다.",
"왜 갑자기 친절해진 걸까요?",
"이유는 다음 날 알게 됐습니다.",
"제가 다른 부서의 팀장으로 승진한다는 소식이 퍼진 겁니다.",
"그제야 깨달았습니다.",
"달라진 건 그 사람의 마음이 아니라, 제 위치를 바라보는 눈이었죠.",
"이런 짧은 이야기가 좋다면, 구독과 좋아요."
]
prompt=("Read exactly the Korean narration below with one steady, low, cinematic Korean male storyteller voice, Charon. "
        "Natural storytelling pace, deliberate pauses between each line for subtitle synchronization. "
        "Do not announce line numbers. Do not omit words, add adlibs or repeat any sentence. "
        "Do not add any intro or music. Read the final like/subscribe line exactly once.\n\n"+ "\n".join(lines))
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
for k in range(4):
 try:
  r=client.models.generate_content(model="gemini-2.5-flash-preview-tts",contents=prompt,config=types.GenerateContentConfig(response_modalities=["AUDIO"],speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
  p=next(x.inline_data for x in r.candidates[0].content.parts if getattr(x,"inline_data",None) and x.inline_data.data)
  data=p.data
  if data.startswith(b"RIFF"): (d/"story_raw.wav").write_bytes(data)
  else:
   m=re.search(r"rate=(\d+)",p.mime_type or "")
   with wave.open(str(d/"story_raw.wav"),"wb") as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(int(m.group(1)) if m else 24000);w.writeframes(data)
  break
 except Exception as e:
  print("TTS_ERROR",k,str(e)[:250],flush=True)
  if k==3:raise
  time.sleep(8)
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),"-y","-hide_banner","-loglevel","error","-i",str(d/"story_raw.wav"),"-af","atempo=1.25","-ar","24000","-ac","1",str(d/"story_charon_125.wav")],check=True)
with wave.open(str(d/"story_charon_125.wav"),"rb") as w: duration=w.getnframes()/w.getframerate()
(d/"script.json").write_text(json.dumps({"lines":lines,"duration":duration},ensure_ascii=False,indent=2),encoding="utf-8")
print("DONE",duration,flush=True)
