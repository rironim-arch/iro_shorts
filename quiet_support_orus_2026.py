#!/usr/bin/env python3
import os,re,subprocess,wave,json
from pathlib import Path
from google import genai
from google.genai import types
out=Path("quiet_support_orus_output");out.mkdir(exist_ok=True)
lines=[
"그날 밤, 저는 휴대폰을 꺼버리려 했습니다.",
"아무에게도 연락하고 싶지 않았거든요.",
"나이가 마흔을 넘으니 참 이상했습니다.",
"힘들다는 말 한마디가 점점 어려워졌습니다.",
"회사에서는 아무렇지 않은 척 웃고,",
"집에 돌아오면 밀린 고지서와 걱정거리들이 저를 기다렸습니다.",
"누군가에게 기대고 싶어도, 다들 자기 살기 바쁜 세상이니까요.",
"그렇게 하루하루 버티며 생각했습니다.",
"결국 인생은 혼자 살아가는 거구나.",
"그런데 어느 날, 정말 모든 걸 내려놓고 싶었던 밤이었습니다.",
"휴대폰에 문자 한 통이 도착했습니다.",
"요즘 목소리가 별로 안 좋더라. 무슨 일 있냐?",
"오래된 친구였습니다.",
"곧이어 어머니에게도 연락이 왔습니다.",
"밥은 잘 챙겨 먹고 다니니?",
"그리고 다음 날 아침,",
"회사 동료가 제 책상에 커피 한 잔을 놓고 갔습니다.",
"어제 많이 힘들어 보이던데, 오늘은 좀 쉬엄쉬엄해요.",
"그때 이상하게 가슴이 먹먹해졌습니다.",
"저는 아무도 제 사정을 모른다고 생각했습니다.",
"그런데 누군가는 제 목소리를 기억하고 있었고,",
"누군가는 제 끼니를 걱정하고 있었고,",
"누군가는 말없이 제 하루를 응원하고 있었습니다.",
"그제야 깨달았습니다.",
"세상에 나를 대신 살아줄 사람은 없어도,",
"내가 무너지지 않기를 바라는 사람은 있다는 걸요.",
"어쩌면 우리는 생각보다 많은 사랑을 받으며 살고 있는지도 모릅니다.",
"오늘도 혼자 버티고 있다고 느끼는 당신.",
"잠시 주변을 돌아보세요.",
"당신이 미처 알아차리지 못한 마음이 곁에 있을지도 모릅니다.",
"공감하셨다면 구독과 좋아요 부탁드립니다."
]
(out/"script.json").write_text(json.dumps({"lines":lines,"voice":"Orus","speed":1.2,"title":"혼자 버티는 줄 알았는데… 그날 알게 된 사실","style":"no horizontal pan, very gentle zoom out only, captions safe area"},ensure_ascii=False,indent=2),encoding="utf8")
prompt=("45~55세 한국 남성 한 명이 자신의 삶을 조용히 회상하듯 읽는 따뜻한 한국어 이야기입니다. "
"목소리는 Gemini Orus 한 명으로만 처음부터 끝까지 유지하고, 자연스럽고 담담한 중년 남성의 억양으로 읽으세요. "
"인용 대사도 같은 사람의 목소리로 읽고 지나치게 과장하거나 울먹이지 마세요. "
"초반엔 무거운 마음을 조심스레 말하고, 후반에는 희망의 여운이 느껴지게 하세요. "
"자연스러운 쉼은 좋지만 너무 늘어지지 마세요. 음악, 효과음, 대본에 없는 말, 추가 설명은 넣지 마세요. "
"다음 텍스트를 원고 그대로 읽으세요:\n\n"+"\n".join(lines))
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
r=client.models.generate_content(model="gemini-2.5-flash-preview-tts",contents=prompt,config=types.GenerateContentConfig(
 response_modalities=["AUDIO"],speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Orus")))))
pkt=next((p.inline_data for p in r.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data),None)
if not pkt:raise RuntimeError("EMPTY_GEMINI_TTS")
raw=out/"quiet_support_orus_original.wav"
if pkt.data.startswith(b"RIFF"):raw.write_bytes(pkt.data)
else:
 m=re.search(r"rate=(\d+)",pkt.mime_type or "")
 with wave.open(str(raw),"wb") as f:
  f.setnchannels(1);f.setsampwidth(2);f.setframerate(int(m.group(1)) if m else 24000);f.writeframes(pkt.data)
fast=out/"quiet_support_orus_120.wav"
subprocess.run(["ffmpeg","-y","-v","error","-i",str(raw),"-af","atempo=1.2,loudnorm=I=-17:TP=-2:LRA=11","-ar","24000","-ac","1",str(fast)],check=True)
subprocess.run(["ffmpeg","-y","-v","error","-i",str(fast),"-b:a","160k",str(out/"quiet_support_orus_120.mp3")],check=True)
with wave.open(str(fast),"rb") as w:duration=w.getnframes()/w.getframerate()
print("ORUS_QUIET_SUPPORT_COMPLETED",json.dumps({"duration":round(duration,2),"sentences":len(lines)}),flush=True)
if duration<45:raise RuntimeError("AUDIO_TOO_SHORT_CHECK_TRUNCATION")
