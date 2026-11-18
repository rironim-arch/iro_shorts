#!/usr/bin/env python3
import os,re,json,wave,subprocess
from pathlib import Path
from google import genai
from google.genai import types
out=Path("two_wolves_orus_output");out.mkdir(exist_ok=True)
lines=[
"어느 날 밤, 한 소년이 할아버지에게 물었습니다.",
"할아버지, 사람은 왜 착한 마음도 있고 나쁜 마음도 있어요?",
"할아버지는 잠시 생각하더니 말했습니다.",
"얘야, 사람의 마음속에는 두 마리의 늑대가 살고 있단다.",
"소년이 눈을 동그랗게 떴습니다.",
"늑대요?",
"그래. 한 마리는 분노와 질투, 미움과 욕심을 먹고 자라는 검은 늑대지.",
"다른 한 마리는 사랑과 이해, 용서와 평화를 먹고 자라는 흰 늑대란다.",
"이 두 늑대는 우리 마음속에서 매일 싸우고 있지.",
"소년은 한참을 생각하다가 물었습니다.",
"그럼 할아버지, 결국 어느 늑대가 이겨요?",
"할아버지는 바로 대답하지 않았습니다.",
"그러다 손자의 어깨에 손을 얹으며 말했습니다.",
"네가 매일 먹이를 주는 늑대가 이긴단다.",
"소년은 저무는 하늘을 바라보았습니다.",
"그날 소년은 한 가지를 깨달았습니다.",
"미워하는 마음에 자꾸 힘을 보태면 미움이 커지고,",
"누군가를 이해하고 용서하려 노력하면 따뜻한 마음도 자라난다는 것을요.",
"어쩌면 우리 인생도 마찬가지 아닐까요?",
"누구나 마음속에 두 마리의 늑대를 품고 살아갑니다.",
"중요한 건 어떤 늑대가 있느냐가 아니라, 오늘 내가 어느 늑대에게 먹이를 주었느냐입니다.",
"여러분은 오늘 어떤 늑대에게 먹이를 주셨나요?",
"공감하셨다면 구독과 좋아요 부탁드립니다."
]
(out/"script.json").write_text(json.dumps({"lines":lines,"voice":"Orus","speed":1.2,"channel":"인생애니사연","title":"두 마리 늑대 중 누가 이길까?","style":"original canyon anime, no campfire/headdress, static or slow zoom only"},ensure_ascii=False,indent=2),encoding="utf8")
prompt=("한 명의 한국 45~55세 남자 전문 이야기꾼이 들려주는 차분한 인생 교훈 동화입니다. "
"처음부터 끝까지 Gemini Orus 남성 음색 하나만 사용하고, 아이와 할아버지 대사에서도 목소리를 크게 바꾸거나 과하게 연기하지 마세요. "
"자연스럽고 편안하게, 지나치게 긴 쉼 없이 한국어 대본을 충실히 읽으세요. "
"마지막 깨달음의 '네가 매일 먹이를 주는 늑대가 이긴단다'는 낮고 따뜻한 목소리로 여운을 주세요. "
"음악과 효과음, 추가 설명, 원고에 없는 문장들은 금지합니다. 대본:\n\n"+"\n".join(lines))
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
r=client.models.generate_content(model="gemini-2.5-flash-preview-tts",contents=prompt,config=types.GenerateContentConfig(
response_modalities=["AUDIO"],speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
 prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Orus")))))
pkt=next((p.inline_data for p in r.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data),None)
if pkt is None: raise RuntimeError("Gemini returned no audio")
raw=out/"two_wolves_orus_original.wav"
if pkt.data.startswith(b"RIFF"): raw.write_bytes(pkt.data)
else:
 m=re.search(r"rate=(\d+)",pkt.mime_type or "")
 with wave.open(str(raw),"wb") as w:
  w.setnchannels(1);w.setsampwidth(2);w.setframerate(int(m.group(1)) if m else 24000);w.writeframes(pkt.data)
fast=out/"two_wolves_orus_120.wav"
subprocess.run(["ffmpeg","-y","-v","error","-i",str(raw),"-af","atempo=1.2,loudnorm=I=-17:TP=-2:LRA=11","-ar","24000","-ac","1",str(fast)],check=True)
subprocess.run(["ffmpeg","-y","-v","error","-i",str(fast),"-b:a","160k",str(out/"two_wolves_orus_120.mp3")],check=True)
with wave.open(str(fast),"rb") as w:dur=w.getnframes()/w.getframerate()
print("TWO_WOLVES_ORUS_OK",json.dumps({"duration":round(dur,2),"lines":len(lines)},ensure_ascii=False),flush=True)
if dur<30:raise RuntimeError("TTS too short")
