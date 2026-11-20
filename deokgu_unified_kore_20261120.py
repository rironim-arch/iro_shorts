#!/usr/bin/env python3
"""One continuous Gemini Kore narration for Deokgu story; no voice drift between individual calls."""
import os, re, wave, subprocess, json
from pathlib import Path
from google import genai
from google.genai import types
OUT=Path("deokgu_unified_output");OUT.mkdir(exist_ok=True)
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
STORY="\n".join(LINES)
prompt=("당신은 한 명의 한국어 여성 다큐멘터리 내레이터입니다. 동일한 성우, 동일한 감정과 음색으로 아래 전체 대본을 한번에 연속해서 또렷하고 차분하게 낭독하세요. "
"따뜻하지만 담담한 목소리를 처음부터 끝까지 균일하게 유지합니다. 모든 문장을 원문 그대로, 순서대로, 생략하거나 덧붙이지 말고 정확히 발음합니다. "
"추가 나레이션, 음악, 효과음, 말 없는 도입부 모두 금지. 중요한 건 전체를 끝까지 낭독하는 것입니다.\n\n"+STORY)
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
r=client.models.generate_content(model="gemini-2.5-flash-preview-tts",contents=prompt,
 config=types.GenerateContentConfig(response_modalities=["AUDIO"],speech_config=types.SpeechConfig(
  voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")))))
data=None
for part in r.candidates[0].content.parts:
 v=getattr(part,"inline_data",None)
 if v is not None and getattr(v,"data",None):data=v;break
if data is None:raise RuntimeError("Single voice generation returned no audio")
raw=OUT/"kore_continuous_raw.wav"
if data.data[:4]==b"RIFF":raw.write_bytes(data.data)
else:
 m=re.search(r"rate=(\d+)",data.mime_type or "")
 with wave.open(str(raw),"wb") as w:
  w.setnchannels(1);w.setsampwidth(2);w.setframerate(int(m.group(1)) if m else 24000);w.writeframes(data.data)
subprocess.run(["ffmpeg","-v","error","-y","-i",str(raw),"-af","atempo=1.25,loudnorm=I=-18:TP=-2:LRA=11,adelay=100,apad=pad_dur=0.3","-ac","1","-ar","24000",str(OUT/"kore_continuous_125.wav")],check=True)
subprocess.run(["ffmpeg","-v","error","-y","-i",str(OUT/"kore_continuous_125.wav"),"-b:a","128k",str(OUT/"kore_continuous_125.mp3")],check=True)
with wave.open(str(OUT/"kore_continuous_125.wav"),"rb") as w: duration=w.getnframes()/w.getframerate()
(OUT/"metadata.json").write_text(json.dumps({"duration":duration,"speed":1.25,"voice":"Gemini Kore, one uninterrupted TTS take","lines":LINES},ensure_ascii=False,indent=2))
print("SUCCESS continuous voice duration",round(duration,2),flush=True)
