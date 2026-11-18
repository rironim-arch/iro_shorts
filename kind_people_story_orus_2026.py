#!/usr/bin/env python3
import os,re,json,wave,subprocess
from pathlib import Path
from google import genai
from google.genai import types

out=Path("kind_people_story_out");out.mkdir(exist_ok=True)
lines=[
"제가 회사에서 실수한 날, 사람들의 진짜 모습이 보였습니다.",
"어릴 때는 어른이 되면 다들 서로 이해하고 배려하며 사는 줄 알았습니다.",
"하지만 사회에 나와 보니 조금 달랐습니다.",
"처음 다니던 회사에서 제가 중요한 서류를 잘못 처리한 날이었습니다.",
"한 사람은 모두 앞에서 저를 나무랐습니다.",
"다른 사람들은 뒤에서 제 이야기를 했습니다.",
"또 누군가는 말했습니다.",
"그러게, 내가 조심하라고 했잖아.",
"정작 어떻게 바로잡아야 하는지는 아무도 알려주지 않았습니다.",
"그날 밤, 혼자 사무실에 남아 서류를 다시 정리하고 있었습니다.",
"그때, 퇴근했던 동료 한 명이 다시 들어왔습니다.",
"그는 말없이 의자를 끌어와 제 옆에 앉더니 이렇게 말했습니다.",
"이 부분부터 같이 해보죠.",
"이상하게 그 짧은 말 한마디에 마음이 놓였습니다.",
"그제야 알았습니다.",
"누군가를 비판하는 데는 말 한마디면 되지만,",
"도와주려면 자기 시간을 내어야 한다는 걸요.",
"그 후 저는 누군가 실수했을 때 먼저 물으려고 합니다.",
"제가 뭘 도와드릴까요?",
"세상에 좋은 사람이 없다고 말하기 전에,",
"나는 누군가에게 어떤 사람이었을까요?",
"공감하셨다면 구독과 좋아요 부탁드립니다."
]
(out/"script.json").write_text(json.dumps({"lines":lines,"voice":"Orus","speed":1.2,"title":"좋은 사람을 알아보는 순간"},ensure_ascii=False,indent=2),encoding="utf8")
prompt=("한 명의 45~55세 한국 남성이 자신이 겪은 사회생활을 조용히 회상하는 감성 사연입니다. "
"Gemini Orus 한 명의 남자 음성으로 처음부터 끝까지 한국어를 자연스럽게 낭독해 주세요. "
"과장한 방송 말투와 어색한 연기를 피하고, 처음에는 담담하게, 마지막은 자기 성찰의 여운을 담으세요. "
"인용 대사에서도 목소리를 바꾸지 마세요. 음악, 효과음, 대본 밖 발화는 금지합니다. "
"자연스럽게 짧은 쉼을 두되 너무 늘어지지 말고 다음 내용만 정확히 읽으세요:\n\n"+"\n".join(lines))
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
r=client.models.generate_content(model="gemini-2.5-flash-preview-tts",contents=prompt,
 config=types.GenerateContentConfig(response_modalities=["AUDIO"],
 speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Orus")))))
packet=next((p.inline_data for p in r.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data),None)
if not packet:raise RuntimeError("NO_TTS_AUDIO")
raw=out/"kind_people_raw.wav"
if packet.data.startswith(b"RIFF"):raw.write_bytes(packet.data)
else:
 m=re.search(r"rate=(\d+)",packet.mime_type or "")
 with wave.open(str(raw),"wb") as w:
  w.setnchannels(1);w.setsampwidth(2);w.setframerate(int(m.group(1)) if m else 24000);w.writeframes(packet.data)
fast=out/"kind_people_orus_120.wav"
subprocess.run(["ffmpeg","-y","-v","error","-i",str(raw),"-af","atempo=1.2,loudnorm=I=-17:TP=-2:LRA=11","-ar","24000","-ac","1",str(fast)],check=True)
subprocess.run(["ffmpeg","-y","-v","error","-i",str(fast),"-b:a","160k",str(out/"kind_people_orus_120.mp3")],check=True)
with wave.open(str(fast),"rb") as w:duration=w.getnframes()/w.getframerate()
print("KIND_PEOPLE_ORUS_OK",json.dumps({"duration":round(duration,2),"lines":len(lines)}),flush=True)
if duration<35:raise RuntimeError("TTS_SHORT_CHECK_TRUNCATION")
