"""Narration v2 of '택배 도둑으로 몰린 경비원' with factual-judgment ending.
One continuous Korean Orus voice, 1.25x, user requested calm shots and corrected ending.
"""
import os,time,re,json,wave,subprocess
from pathlib import Path
from google import genai
from google.genai import types
import imageio_ffmpeg
D=Path("guard_parcel_revised_audio");D.mkdir(exist_ok=True)
lines=[
"택배 도둑 잡았다! 아파트 주민들이 한 경비원 할아버지를 둘러쌌습니다.",
"며칠째 택배가 사라졌는데, 한 남자가 할아버지가 상자를 가져가는 걸 봤다고 했죠.",
"할아버지는 억울하다는 듯 고개를 저었습니다.",
"저는 훔친 게 아닙니다. 제 말을 좀 들어주세요.",
"하지만 주민들은 경비실 CCTV부터 확인하자며 몰아붙였습니다.",
"화면 속에는 정말 할아버지가 택배 상자를 들고 엘리베이터에 타는 모습이 찍혀 있었죠.",
"거봐요! 제가 봤다니까요!",
"그때 다른 경비원이 조용히 말했습니다.",
"잠깐만요. 영상을 십 분 전부터 돌려보시죠.",
"영상을 되감자 모자를 눌러쓴 남자가 택배를 훔쳐 계단으로 달아나는 모습이 보였습니다.",
"할아버지는 그 남자를 쫓다가, 그가 버린 상자를 주워 경비실에 가져다 놓았던 겁니다.",
"그런데 확대된 CCTV 화면을 본 주민들이 얼어붙었습니다.",
"택배를 훔친 남자는 바로 처음 할아버지를 도둑으로 몰았던 그 주민이었으니까요.",
"CCTV에서 진범의 얼굴이 드러나자, 주민들은 아무 말도 하지 못했습니다.",
"그 남자가 고개를 숙이자 할아버지가 조용히 말했습니다.",
"의심하실 수는 있습니다. 하지만 확인도 하기 전에 도둑이라고 단정하지는 말아 주세요.",
"그날 아파트 게시판에는 할아버지에게 보내는 사과문이 붙었습니다.",
"눈에 보이는 장면이 언제나 진실의 전부는 아닙니다.",
"이 내용이 마음에 드셨으면 구독과 좋아요 해주세요."
]
assert sum(t.count("구독과 좋아요") for t in lines)==1
prompt=("You are a professional Korean voice actor with the deep adult male Orus voice. "
 "Tell this original fictional Korean apartment security guard mystery in ONE continuous take. "
 "Clear, grounded, sincere and slightly suspenseful, never overacting; the ending is respectful and realistic. "
 "Pause naturally between EVERY provided newline; these deliberate pauses allow scene and subtitle alignment. "
 "Read every Korean sentence exactly once, without paraphrases, additions or omissions, no introductions. "
 "The CTA at the end must appear exactly ONCE and only after the story concludes. "
 "No music, no sound effects; narration only. Do not read instructions. "
 "Aim for natural easy-to-understand pacing.\\n"
 "KOREAN SCRIPT:\\n"+"\n".join(lines))
c=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
raw=D/"raw.wav"
for attempt in range(5):
 try:
  r=c.models.generate_content(model="gemini-2.5-flash-preview-tts",contents=prompt,
    config=types.GenerateContentConfig(response_modalities=["AUDIO"],
       speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
          prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Orus")))))
  p=next(x.inline_data for x in r.candidates[0].content.parts if getattr(x,"inline_data",None) and x.inline_data.data)
  if p.data.startswith(b"RIFF"):raw.write_bytes(p.data)
  else:
    m=re.search(r"rate=(\d+)",p.mime_type or "")
    with wave.open(str(raw),"wb") as w:
      w.setnchannels(1);w.setsampwidth(2);w.setframerate(int(m.group(1)) if m else 24000);w.writeframes(p.data)
  break
 except Exception as exc:
  print("RETRY",attempt,str(exc)[:230],flush=True)
  if attempt==4:raise
  time.sleep(12*(attempt+1))
target=D/"guard_parcel_orus_v2_125.wav"
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),"-y","-hide_banner","-loglevel","error",
 "-i",str(raw),"-af","atempo=1.25","-ar","24000","-ac","1",str(target)],check=True)
with wave.open(str(target),"rb") as w: duration=w.getnframes()/w.getframerate()
if not 40<duration<135:raise ValueError(f"Invalid TTS duration {duration}")
(D/"script.json").write_text(json.dumps({"lines":lines,"voice":"Orus","speed":1.25,"duration":duration},ensure_ascii=False,indent=2),encoding="utf-8")
raw.unlink()
print("AUDIO_V2_READY",duration,target.stat().st_size,flush=True)
