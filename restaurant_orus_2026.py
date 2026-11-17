#!/usr/bin/env python3
from google import genai
from google.genai import types
from pathlib import Path
import os, subprocess, re, json, wave
out=Path("restaurant_orus_output");out.mkdir(exist_ok=True)
lines=[
"제가 운영하던 음식점 장사가 어려워지자, 이상한 일이 생겼습니다.",
"저를 불편해하던 친구들이, 갑자기 다시 친절해진 겁니다.",
"몇 년 전만 해도 제 가게는 정말 잘됐습니다.",
"저녁마다 빈자리가 없었고, 예약 전화가 쉴 새 없이 울렸죠.",
"솔직히 저도 신이 났습니다.",
"야, 이번 달 매출 정말 잘 나왔어.",
"친구들 앞에서 자랑도 많이 했습니다.",
"그런데 친구들 표정이 조금씩 달라졌습니다.",
"야, 돈 좀 번다고 잘난 척하네.",
"장사가 언제까지 잘되겠냐?",
"웃으면서 하는 말인데도, 이상하게 가슴에 남았습니다.",
"그러다 코로나가 시작됐습니다.",
"손님은 줄었고, 텅 빈 가게에 혼자 앉아 있는 날이 많아졌습니다.",
"월세와 인건비는 그대로인데, 매출은 계속 내려갔습니다.",
"문을 닫은 건 아니었습니다. 하지만 하루하루 버티는 기분이었죠.",
"그런데 그때부터 친구들이 달라졌습니다.",
"야, 요즘 힘들지? 밥이나 먹자.",
"괜찮아. 다시 좋아질 거야.",
"제가 잘나갈 때는 차갑던 말투가 다시 다정해진 겁니다.",
"고맙기도 했지만, 마음 한구석이 씁쓸했습니다.",
"내가 잘될 때는 왜 불편해하고, 힘들어지니까 편해진 걸까?",
"물론, 그중에는 진심으로 걱정해 준 친구도 있었겠죠.",
"하지만 저는 그 일을 겪고 자랑하는 습관을 조금씩 버렸습니다.",
"내가 잘된다는 걸, 누군가에게 증명할 필요는 없으니까요.",
"이젠 압니다. 힘들 때 내 곁을 지켜주는 사람도 소중하지만,",
"내가 잘될 때 진심으로 기뻐해 주는 사람은 더 귀하다는 걸요.",
"공감하셨다면 구독과 좋아요 부탁드립니다."
]
(out/"script.json").write_text(json.dumps({"lines":lines,"voice":"Orus","speed":1.2,"project":"인생애니사연","title":"내가 힘들어지자 친구들이 다시 친절해졌습니다","genre":"실제 경험 기반 각색"},ensure_ascii=False,indent=2),encoding="utf8")
prompt=("지금부터 한 명의 한국 40대 후반 남성이 자신의 과거를 후회와 씁쓸함을 담아 말하는 1인칭 수필 내레이션입니다. "
"Gemini Orus 남자 목소리 한 사람만 처음부터 끝까지 유지하세요. "
"직업 성우처럼 과장하거나 웅변하지 말고, 평범한 45~55세 한국 남성이 낮은 목소리로 조용히 경험담을 들려주듯 자연스럽고 담백하게 읽으세요. "
"친구의 인용 대사도 절대 다른 목소리로 연기하지 마세요. 웃음, 음악, 효과음, 설명 추가를 금합니다. "
"문장 사이에 짧은 자연스러운 쉼만 두고 대본을 정확히 읽으세요.\n\n"+"\n".join(lines))
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
r=client.models.generate_content(model="gemini-2.5-flash-preview-tts",contents=prompt,config=types.GenerateContentConfig(
response_modalities=["AUDIO"],speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Orus")))))
pkt=next((p.inline_data for p in r.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data),None)
if not pkt: raise RuntimeError("NO_AUDIO")
wav=out/"restaurant_orus_raw.wav"
if pkt.data.startswith(b"RIFF"): wav.write_bytes(pkt.data)
else:
 m=re.search(r"rate=(\\d+)",pkt.mime_type or "")
 with wave.open(str(wav),"wb") as w:
  w.setnchannels(1);w.setsampwidth(2);w.setframerate(int(m.group(1)) if m else 24000);w.writeframes(pkt.data)
# Save original voice if ffmpeg missing; do tempo locally
print("ORUS_RAW_AUDIO_READY",wav.stat().st_size,flush=True)
subprocess.run(["ffmpeg","-y","-v","error","-i",str(wav),"-af","atempo=1.2,loudnorm=I=-17:TP=-2:LRA=11","-ar","24000","-ac","1",str(out/"restaurant_orus_120.wav")],check=True)
subprocess.run(["ffmpeg","-y","-v","error","-i",str(out/"restaurant_orus_120.wav"),"-b:a","160k",str(out/"restaurant_orus_120.mp3")],check=True)
with wave.open(str(out/"restaurant_orus_120.wav"),"rb") as w: duration=w.getnframes()/w.getframerate()
print("ORUS_RESTAURANT_OK",json.dumps({"duration":round(duration,2),"nlines":len(lines)}),flush=True)
if duration<50:raise RuntimeError("VOICE_TOO_SHORT")
