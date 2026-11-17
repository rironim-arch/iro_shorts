#!/usr/bin/env python3
import os, re, subprocess, json, wave
from pathlib import Path
from google import genai
from google.genai import types
out=Path("cat_gratitude_kore_output");out.mkdir(exist_ok=True)
lines=[
"그날 새벽, 고양이 한 마리가 이웃집 대문을 미친 듯이 긁었습니다.",
"사람들은 그저 배가 고픈 줄 알았습니다.",
"일 년 전, 비가 쏟아지던 어느 날.",
"마을 끝집 할머니는 대문 앞에서 떨고 있던 어린 고양이를 발견했습니다.",
"할머니는 젖은 몸을 수건으로 감싸고 따뜻한 밥을 내주셨습니다.",
"그날부터 고양이는 할머니의 그림자가 됐습니다.",
"마당에 나서면 따라오고, 툇마루에 앉으면 무릎에 올라왔죠.",
"그러던 어느 날, 혼자 있던 할머니가 갑자기 쓰러지셨습니다.",
"고양이는 할머니 곁을 맴돌며 울었습니다.",
"아무리 불러도 일어나지 않자, 대문 밖으로 달려갔죠.",
"그리고 옆집 대문을 온 힘을 다해 긁기 시작했습니다.",
"문을 연 이웃이 다가오자, 고양이는 몇 걸음 뛰다가 자꾸 뒤를 돌아봤습니다.",
"이상하다고 생각한 이웃이 따라갔습니다.",
"그곳에 할머니가 쓰러져 계셨습니다.",
"다행히 할머니는 제때 병원으로 옮겨져 무사했습니다.",
"집에 돌아온 날, 할머니는 고양이를 꼭 안고 속삭였습니다.",
"내가 널 살린 줄 알았는데… 네가 나를 살렸구나.",
"작은 친절 하나가, 결국 생명을 구했습니다.",
"마음에 남으셨다면 구독과 좋아요 부탁드립니다."
]
(out/"script.json").write_text(json.dumps({"lines":lines,"voice":"Kore","speed":1.25,"title":"고양이의 보은"},ensure_ascii=False,indent=2),encoding="utf8")
prompt="다음 한국어 창작 애니메이션 사연을 여성 성우 한 명이 차분하게 들려주는 이야기로 읽어주세요. 전 구간에 Gemini Kore 하나의 목소리만 유지합니다. 아주 자연스러운 한국어 표준 발음, 부드럽고 따뜻한 목소리, 담담한 회상 톤, 영화 같은 절제된 감정선, 여운 있는 짧은 쉼. 억지로 울먹이거나 과장된 나레이션, 인물별 연기, 다른 목소리, 음악과 효과음은 절대 금지합니다. 다음 원고만 정확하게 읽고 원고 밖의 말을 덧붙이지 마세요.\n\n"+"\n".join(lines)
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
r=client.models.generate_content(model="gemini-2.5-flash-preview-tts",contents=prompt,
 config=types.GenerateContentConfig(response_modalities=["AUDIO"],
 speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")))))
packet=next((p.inline_data for p in r.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data),None)
if packet is None: raise RuntimeError("NO_AUDIO_DATA")
wav=out/"cat_kore_original.wav"
if packet.data.startswith(b"RIFF"):wav.write_bytes(packet.data)
else:
 m=re.search(r"rate=(\\d+)",packet.mime_type or "")
 with wave.open(str(wav),"wb") as f:
  f.setnchannels(1);f.setsampwidth(2);f.setframerate(int(m.group(1)) if m else 24000);f.writeframes(packet.data)
fast=out/"cat_kore_125.wav"
subprocess.run(["ffmpeg","-y","-v","error","-i",str(wav),"-af","atempo=1.25,loudnorm=I=-17:TP=-2:LRA=11","-ar","24000","-ac","1",str(fast)],check=True)
subprocess.run(["ffmpeg","-y","-v","error","-i",str(fast),"-b:a","160k",str(out/"cat_kore_125.mp3")],check=True)
with wave.open(str(fast),"rb") as f:seconds=f.getnframes()/f.getframerate()
print("CAT_KORE_VOICE_READY",json.dumps({"seconds":round(seconds,2),"sentences":len(lines)}),flush=True)
if seconds<30:raise RuntimeError("SPEECH_TOO_SHORT_CHECK_TRUNCATION")
