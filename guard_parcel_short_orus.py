"""One-take Orus TTS: accused Korean apartment guard and stolen parcel twist.
A fully fictional 2D webtoon story.
"""
import os,time,re,wave,json,subprocess
from pathlib import Path
from google import genai
from google.genai import types
import imageio_ffmpeg

out=Path("guard_parcel_audio");out.mkdir(exist_ok=True)
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
"그 남자가 고개를 숙이자 할아버지가 말했습니다.",
"나이가 많다고 함부로 의심하지 마세요. 저도 누군가의 아버지입니다.",
"그날 아파트 게시판에는 사과문이 붙었습니다.",
"사람을 판단하기 전에, 사실부터 확인해야 합니다.",
"이 내용이 마음에 드셨으면 구독과 좋아요 해주세요."
]
assert sum(x.count("구독과 좋아요") for x in lines)==1
text="\n".join(lines)
prompt=("You are a professional Korean male storyteller, voice Orus. Read the original dramatic Korean webtoon script exactly in ONE continuous steady single take, "
        "as an expressive yet restrained narration. Slight tension in the opening and reveal, dignified warm emotion on the grandfather's final words. "
        "Speak in natural modern standard Korean with distinct intentional pauses between paragraphs; never rush. "
        "Keep the SAME Orus voice all the way through; quoted dialogue is narrated rather than switching voices. "
        "No music, no effects, no extra introductions or closing. Do not repeat any words or speak instructions. "
        "The final subscribe-and-like reminder is said exactly ONCE only at the very end.\\nSCRIPT:\\n"+text)
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
raw=out/"guard_orus_raw.wav"
for attempt in range(5):
 try:
  r=client.models.generate_content(model="gemini-2.5-flash-preview-tts",contents=prompt,
    config=types.GenerateContentConfig(response_modalities=["AUDIO"],speech_config=types.SpeechConfig(
      voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Orus")))))
  p=next(x.inline_data for x in r.candidates[0].content.parts if getattr(x,"inline_data",None) and x.inline_data.data)
  if p.data.startswith(b"RIFF"): raw.write_bytes(p.data)
  else:
   m=re.search(r"rate=(\d+)",p.mime_type or "")
   with wave.open(str(raw),"wb") as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(int(m.group(1)) if m else 24000);w.writeframes(p.data)
  break
 except Exception as e:
  print("RETRY",attempt,str(e)[:250],flush=True)
  if attempt==4:raise
  time.sleep(12*(attempt+1))
ff=imageio_ffmpeg.get_ffmpeg_exe()
audio=out/"guard_parcel_orus_125.wav"
subprocess.run([ff,"-y","-hide_banner","-loglevel","error","-i",str(raw),"-af","atempo=1.25","-ar","24000","-ac","1",str(audio)],check=True)
with wave.open(str(audio),"rb") as w: duration=w.getnframes()/w.getframerate()
if not 35<duration<130:raise ValueError(f"Unexpected audio duration {duration}")
(out/"script.json").write_text(json.dumps({"title":"택배 도둑으로 몰린 경비원 할아버지… CCTV 속 진범","lines":lines,"duration":duration,"voice":"Orus","speed":1.25,"fiction":True},ensure_ascii=False,indent=2),encoding="utf8")
raw.unlink()
print("READY",duration,audio.stat().st_size,flush=True)
