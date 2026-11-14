"""Original Korean webtoon Shorts: one continuous female Kore narration.
Creates only review audio; no publication.
"""
import os, re, wave, time, json, subprocess
from pathlib import Path
from google import genai
from google.genai import types
import imageio_ffmpeg
D=Path("guard_and_child_audio")
D.mkdir(exist_ok=True)
lines=[
"매일 아침, 경비실 창문을 두드리는 여자아이가 있었습니다.",
"할아버지! 오늘도 힘내세요!",
"수십 년 일한 경비원에게 그 인사는 하루 중 가장 기다려지는 순간이었죠.",
"그런데 어느 월요일부터 아이가 보이지 않았습니다.",
"화요일도, 수요일도. 하루가 일주일이 됐습니다.",
"혹시 무슨 일이 생긴 건 아닐까. 할아버지는 매일 같은 시간 문밖을 바라봤습니다.",
"그러던 눈 내리는 아침, 경비실 문 앞에 작은 봉투가 놓였습니다.",
"그 안에는 파란 털장갑과 삐뚤빼뚤한 글씨의 편지가 있었죠.",
"할아버지, 저 갑자기 이사 갔어요. 인사도 못 해서 미안해요.",
"엄마가 힘든 날엔 할아버지가 웃어주신 이야기를 하며 같이 웃었어요.",
"이제 제가 인사 못 하니까, 이 장갑이 대신 손을 따뜻하게 해줬으면 좋겠어요.",
"할아버지는 장갑을 낀 채 한동안 그 자리에 서 있었습니다.",
"어쩌면 우리가 건넨 작은 인사가 누군가에게는 하루를 견디는 힘이 될지도 모릅니다.",
"이 내용이 마음에 드셨으면 구독과 좋아요 해주세요."
]
text="\n".join(lines)
assert text.count("구독과 좋아요")==1
prompt=("You are one Korean female voice narrator, Kore, reading a fictional emotionally moving human story. "
 "Perform the supplied Korean story in one single take with a calm sincere storyteller voice, "
 "intimate and humane, medium natural speed, soft emotional detail but never exaggerated. "
 "The quoted child's and letter's words should be slightly warm but remain in the SAME Kore voice. "
 "Maintain brief natural pauses between each supplied line to permit subtitle cuts. "
 "Do not read any extra words, omit or repeat any sentence, do not say instructions, "
 "do not generate music or sound effects. Speak the final call to action ONCE and ONLY at the end.\n\n"+text)
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
raw=D/"raw.wav"
for attempt in range(5):
 try:
  result=client.models.generate_content(
    model="gemini-2.5-flash-preview-tts",contents=prompt,
    config=types.GenerateContentConfig(response_modalities=["AUDIO"],
      speech_config=types.SpeechConfig(
       voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")))))
  part=next(p.inline_data for p in result.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data)
  b=part.data
  if b.startswith(b"RIFF"):raw.write_bytes(b)
  else:
    match=re.search(r"rate=(\d+)",part.mime_type or "")
    sr=int(match.group(1)) if match else 24000
    with wave.open(str(raw),"wb") as w:
     w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(b)
  break
 except Exception as e:
  print("TTS_RETRY",attempt,str(e)[:180],flush=True)
  if attempt==4:raise
  time.sleep(9*(attempt+1))
audio=D/"guard_child_kore_125.wav"
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),"-y","-hide_banner","-loglevel","error","-i",str(raw),"-af","atempo=1.25","-ar","24000","-ac","1",str(audio)],check=True,timeout=120)
with wave.open(str(audio),"rb") as w: duration=w.getnframes()/w.getframerate()
if not 35<duration<100:raise RuntimeError(f"Out of range {duration}")
(D/"script.json").write_text(json.dumps({"lines":lines,"duration":round(duration,3),"voice":"Kore","speed":1.25,"fiction":True},ensure_ascii=False,indent=2),encoding="utf-8")
print("AUDIO_READY",round(duration,2),audio.stat().st_size,flush=True)
