#!/usr/bin/env python3
import os,re,subprocess,wave,json
from pathlib import Path
from google import genai
from google.genai import types

out=Path("mutt_ww1_kore_output"); out.mkdir(exist_ok=True)
lines=[
"총알이 날아다니던 전쟁터. 작은 검은 강아지 한 마리가 참호로 향했습니다.",
"더 놀라운 건, 그 등에 묶여 있던 작은 상자였습니다.",
"그 안에 들어 있던 건 총알도, 약도 아니었습니다.",
"1918년, 프랑스. 이 강아지의 이름은 머트였습니다.",
"머트는 미군 제11공병연대 병사들에게 물건을 전하던 프렌치불도그였죠.",
"그가 등에 싣고 다녔던 건, 놀랍게도 담배였습니다.",
"당시 전쟁터에서 담배는 지친 병사들에게 잠깐의 위안을 주는 물건이었습니다.",
"포성이 멈추지 않는 참호. 병사들은 내일을 장담할 수 없었습니다.",
"그곳으로 작은 머트가 상자를 짊어진 채 찾아왔습니다.",
"온몸에 진흙을 묻힌 작은 손님. 병사들은 잠시 긴장을 내려놓을 수 있었겠죠.",
"하지만 머트에게도 전쟁터는 안전한 곳이 아니었습니다.",
"전해지는 기록에 따르면, 머트는 임무를 다니던 중 두 차례나 부상을 입었습니다.",
"그럼에도 머트의 모습은 한 장의 사진으로 남았습니다.",
"등에 물건을 지고, 두 귀를 바짝 세운 채 카메라를 바라보는 작은 강아지.",
"사람들이 서로를 해치던 시대에도, 작은 동물 하나가 전한 위로는 있었습니다.",
"그 누구보다 작았지만, 전쟁터에서 결코 작은 존재가 아니었던 강아지.",
"그의 이름은, 머트였습니다.",
"마음에 남으셨다면 구독과 좋아요 부탁드립니다."
]
(out/"script.json").write_text(json.dumps({"lines":lines,"voice":"Kore","speed":1.25,"project":"인생애니사연","title":"총알이 쏟아지는 전쟁터에 강아지를 보낸 이유","historical_basis":"Mutt, YMCA cigarette dog, 11th Engineers, WWI"},ensure_ascii=False,indent=2),encoding="utf8")
prompt=("한국어 역사 감동 숏츠 영상 대본입니다. 하나의 여성 중저음 Kore 목소리로, 생생하고 담담한 다큐멘터리 형식으로 읽으세요. "
"초반 3문장은 위험한 전쟁터에 놓인 동물에 대한 긴장감과 궁금증을 담되 말을 끊지 마세요. "
"중반은 자연스럽고 명료하게, 마지막 4문장은 절제된 감정과 여운을 갖고 조금 천천히 읽으세요. "
"지나치게 밝게 읽거나 오열, 성우 연기, 노래, 효과음, 추가 설명을 하지 마세요. 한 명의 목소리로만, 정확히 다음 원고를 낭독하세요.\n\n"+"\n".join(lines))
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
r=client.models.generate_content(model="gemini-2.5-flash-preview-tts",contents=prompt,
    config=types.GenerateContentConfig(response_modalities=["AUDIO"],speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")))))
packet=next((p.inline_data for p in r.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data),None)
if not packet: raise RuntimeError("GEMINI_TTS_EMPTY")
raw=out/"mutt_kore_original.wav"
if packet.data.startswith(b"RIFF"):raw.write_bytes(packet.data)
else:
    m=re.search(r"rate=(\d+)",packet.mime_type or "")
    with wave.open(str(raw),"wb") as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(int(m.group(1)) if m else 24000);f.writeframes(packet.data)
print("GEMINI_KORE_ORIGINAL_SAVED",raw.stat().st_size,flush=True)
fast=out/"mutt_kore_125.wav"
subprocess.run(["ffmpeg","-y","-v","error","-i",str(raw),"-af","atempo=1.25,loudnorm=I=-17:TP=-2:LRA=11","-ar","24000","-ac","1",str(fast)],check=True)
subprocess.run(["ffmpeg","-y","-v","error","-i",str(fast),"-b:a","160k",str(out/"mutt_kore_125.mp3")],check=True)
with wave.open(str(fast),"rb") as f: duration=f.getnframes()/f.getframerate()
if duration<35:raise RuntimeError("AUDIO_TOO_SHORT_CHECK_TRUNCATION")
print("MUTT_KORE_COMPLETED",json.dumps({"duration":round(duration,2),"lines":len(lines)},ensure_ascii=False),flush=True)
