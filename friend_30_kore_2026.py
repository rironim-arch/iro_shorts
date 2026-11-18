#!/usr/bin/env python3
import os,re,subprocess,wave,json
from pathlib import Path
from google import genai
from google.genai import types
out=Path("friend_30_kore_output");out.mkdir(exist_ok=True)
lines=[
"10년을 함께한 친구였습니다.",
"그런데 문자 한 통 때문에 그 친구를 다시 보게 됐습니다.",
"어느 날 친구가 급하게 전화했습니다.",
"30만 원만 빌려줘. 다음 주 월요일에 꼭 갚을게.",
"저는 망설이지 않고 보내줬습니다.",
"그런데 약속한 날이 지나도 연락이 없었습니다.",
"며칠 뒤 친구의 SNS를 보다가 깜짝 놀랐습니다.",
"고급 호텔에서 웃고 있는 사진이 올라와 있었거든요.",
"그래도 조심스럽게 물었습니다.",
"지난번 돈은 언제쯤 줄 수 있어?",
"그런데 돌아온 답장은 뜻밖이었습니다.",
"야, 우리가 10년 친구인데 고작 30만 원 때문에 이러냐?",
"순간 말문이 막혔습니다.",
"저는 친구니까 약속을 지킬 거라 믿었는데,",
"친구는 친구니까 약속을 안 지켜도 된다고 생각했던 겁니다.",
"마지막으로 답장을 보냈습니다.",
"돈보다 네가 한 약속이 더 중요했어.",
"그날 깨달았습니다.",
"오래된 친구가 반드시 좋은 친구는 아니라는 걸.",
"진짜 우정은 함께한 세월보다 서로를 대하는 태도에 있다는 걸요.",
"여러분이라면 어떻게 하셨을까요?",
"공감하셨다면 구독과 좋아요 부탁드립니다."
]
(out/"script.json").write_text(json.dumps({"lines":lines,"voice":"Kore","speed":1.25,"channel":"인생애니사연"},ensure_ascii=False,indent=2),encoding="utf8")
prompt="한국 여성 성우가 자신의 오랜 친구와 사이가 틀어진 사연을 조용히 회상하는 1인칭 한국어 내레이션입니다. 여성 Kore 목소리 하나만 사용하세요. 말투는 진짜 사람처럼 담백하고 따뜻하며 대사에서만 짧고 절제된 감정 표현을 합니다. 친구의 인용문도 같은 Kore 목소리로 읽고 다른 사람 목소리는 쓰지 마세요. 문장 사이 자연스럽고 짧은 쉼을 주세요. 음악, 효과음, 울먹임, 과장, 추가 대사는 금지합니다. 다음 원고만 정확하게 읽으세요:\n\n"+"\n".join(lines)
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
r=client.models.generate_content(model="gemini-2.5-flash-preview-tts",contents=prompt,config=types.GenerateContentConfig(response_modalities=["AUDIO"],speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")))))
pkt=next((p.inline_data for p in r.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data),None)
if not pkt:raise RuntimeError("GEMINI_AUDIO_MISSING")
raw=out/"friend_30_kore_raw.wav"
if pkt.data.startswith(b"RIFF"):raw.write_bytes(pkt.data)
else:
 m=re.search(r"rate=(\d+)",pkt.mime_type or "")
 with wave.open(str(raw),"wb") as f:
  f.setnchannels(1);f.setsampwidth(2);f.setframerate(int(m.group(1)) if m else 24000);f.writeframes(pkt.data)
subprocess.run(["ffmpeg","-y","-v","error","-i",str(raw),"-af","atempo=1.25,loudnorm=I=-17:TP=-2:LRA=11","-ar","24000","-ac","1",str(out/"friend_30_kore_125.wav")],check=True)
subprocess.run(["ffmpeg","-y","-v","error","-i",str(out/"friend_30_kore_125.wav"),"-b:a","160k",str(out/"friend_30_kore_125.mp3")],check=True)
with wave.open(str(out/"friend_30_kore_125.wav"),"rb") as w:duration=w.getnframes()/w.getframerate()
print("FRIEND_30_KORE_DONE",json.dumps({"seconds":round(duration,2),"lines":len(lines)}),flush=True)
if duration<25:raise RuntimeError("TTS_TOO_SHORT")
