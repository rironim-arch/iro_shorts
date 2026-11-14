"""One continuous Kore voice recording for original convenience-store emotional webtoon story."""
import os, re, wave, time, json, subprocess
from pathlib import Path
from google import genai
from google.genai import types
import imageio_ffmpeg

D=Path("triangle_rice_story_assets")
D.mkdir(exist_ok=True)
lines=[
 "매일 밤 열한 시, 한 할머니가 가장 싼 삼각김밥만 사 갔습니다.",
 "비가 오는 날에도, 추운 날에도, 늘 같은 삼각김밥이었죠.",
 "직원은 마음이 쓰여 조심스럽게 물었습니다.",
 "할머니, 따뜻한 도시락은 어떠세요?",
 "할머니는 웃으며 말했죠. 이거 하나면 충분해요.",
 "어느 날, 비에 흠뻑 젖은 할머니가 또 찾아왔습니다.",
 "직원은 따뜻한 도시락을 계산대에 올려놓았습니다.",
 "오늘은 제가 드릴게요.",
 "그런데 할머니는 도시락 대신, 삼각김밥을 꼭 쥐었습니다.",
 "사실은 우리 영감이랑 처음 만났던 날, 돈이 없어서 이거 하나를 나눠 먹었어요.",
 "지금은 먼저 떠났지만, 이걸 먹으면 그때가 다시 생각나요.",
 "직원은 아무 말도 할 수 없었습니다.",
 "누군가에게 평범한 한 끼가, 다른 누군가에겐 평생 잊지 못할 기억이니까요.",
 "이 내용이 마음에 드셨으면 구독과 좋아요 해주세요."
]
full="\n".join(lines)
assert full.count("구독과 좋아요")==1
prompt=(
 "Read this Korean story in one single continuous voice take. Use the single warm Korean female voice Kore for all lines; "
 "narrate quoted characters softly as part of the same story, without changing voice or creating multiple characters. "
 "The storytelling is restrained, warmly emotional and natural, never melodramatic. "
 "Include subtle natural pauses between each sentence so the editor can cut scenes. "
 "Read exactly the supplied Korean words, no greeting, title, extra lines, repeated sentences, music, sound effects, or spoken instructions. "
 "The like-and-subscribe sentence is only at the very end, exactly once.\nSTORY:\n"+full
)
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
raw=D/"kore_original.wav"
for attempt in range(5):
 try:
  result=client.models.generate_content(
   model="gemini-2.5-flash-preview-tts",contents=prompt,
   config=types.GenerateContentConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
      prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")))))
  part=next(x.inline_data for x in result.candidates[0].content.parts if getattr(x,"inline_data",None) and x.inline_data.data)
  b=part.data
  if b.startswith(b"RIFF"):raw.write_bytes(b)
  else:
   m=re.search(r"rate=(\d+)",part.mime_type or "")
   with wave.open(str(raw),"wb") as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(int(m.group(1)) if m else 24000);w.writeframes(b)
  break
 except Exception as e:
  print("RETRY",attempt,str(e)[:250],flush=True)
  if attempt==4:raise
  time.sleep(12*(attempt+1))
FF=imageio_ffmpeg.get_ffmpeg_exe()
audio=D/"grandmother_store_kore_125.wav"
subprocess.run([FF,"-y","-hide_banner","-loglevel","error","-i",str(raw),"-af","atempo=1.25","-ar","24000","-ac","1",str(audio)],check=True,timeout=120)
with wave.open(str(audio),"rb") as w:duration=w.getnframes()/w.getframerate()
if not 30<duration<110:raise RuntimeError(f"Unexpected duration {duration}")
(D/"manifest.json").write_text(json.dumps({"voice":"Kore","speed":1.25,"duration":duration,"lines":lines,"fiction":True},ensure_ascii=False,indent=2),encoding="utf8")
print("VOICE_READY",round(duration,3),"s",audio.stat().st_size,"bytes",flush=True)
