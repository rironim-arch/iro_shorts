#!/usr/bin/env python3
import os,re,subprocess,wave,json
from pathlib import Path
from google import genai
from google.genai import types

out=Path("rural_dog_kore_output"); out.mkdir(exist_ok=True)
script=[
"밖에도 못 나가던 강아지가, 할아버지 제삿날 사라졌습니다.",
"우리 강아지는 정말 소심한 아이였습니다.",
"시골집 대문 여는 소리만 나면, 툇마루 밑으로 숨어버렸죠.",
"그런데 할아버지 곁에만 있으면 달랐습니다.",
"해가 뜨면 발치에 앉고, 해가 지면 무릎에 얼굴을 묻었습니다.",
"그러던 어느 날, 할아버지가 세상을 떠나셨습니다.",
"아이는 한동안 빈 툇마루만 바라보았습니다.",
"그리고 일 년 뒤, 할아버지 제삿날 아침.",
"언제나 같은 자리에 있던 강아지가 사라졌습니다.",
"가족들은 마당과 헛간, 밭길까지 샅샅이 뒤졌습니다.",
"한 번도 혼자 집 밖으로 나간 적이 없는 아이였으니까요.",
"한참을 찾던 끝에, 가족들은 뒷산으로 올라갔습니다.",
"그리고 그곳에서, 강아지를 발견했습니다.",
"할아버지 묘비 앞에 조용히 엎드려 있었던 겁니다.",
"강아지는 누가 부르는 소리에도 한동안 움직이지 않았습니다.",
"그 모습을 본 가족들은 한참 동안 아무 말도 하지 못했습니다.",
"아… 할아버지 배웅하러 갔구나.",
"그날 알았습니다. 사랑하는 마음은 말없이도 남는다는 걸요.",
"마음에 남으셨다면 구독과 좋아요 부탁드립니다."
]
text="\n".join(script)
(out/"script.json").write_text(json.dumps({"lines":script,"voice":"Kore","speed":1.25,"title":"제삿날 사라진 강아지"},ensure_ascii=False,indent=2),encoding="utf-8")
prompt="다음은 감정을 절제한 한국어 창작 사연입니다. 한 명의 한국인 여성 이야기꾼이 들려주는 것처럼, 부드럽고 맑은 중저음의 Gemini Kore 목소리로만 처음부터 끝까지 읽으세요. 느긋하지만 지루하지 않고 문장마다 감정의 여운을 짧게 남기세요. 절대 울먹이거나 과장해서 연기하지 마세요. 인물의 대사도 모두 같은 성우의 목소리로 읽고, 음악과 효과음을 넣지 마세요. 아래 대사 외 다른 말을 덧붙이지 마세요:\n\n"+text
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
r=client.models.generate_content(
    model="gemini-2.5-flash-preview-tts",
    contents=prompt,
    config=types.GenerateContentConfig(response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")))))
pkt=next((p.inline_data for p in r.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data),None)
if not pkt: raise RuntimeError("EMPTY_GEMINI_KORE_AUDIO")
raw=out/"dog_kore_original.wav"
if pkt.data.startswith(b"RIFF"): raw.write_bytes(pkt.data)
else:
  match=re.search(r"rate=(\d+)",pkt.mime_type or "")
  with wave.open(str(raw),"wb") as f:
    f.setnchannels(1); f.setsampwidth(2); f.setframerate(int(match.group(1)) if match else 24000); f.writeframes(pkt.data)
fast=out/"dog_kore_125.wav"
subprocess.run(["ffmpeg","-y","-v","error","-i",str(raw),"-af","atempo=1.25,loudnorm=I=-17:TP=-2:LRA=11","-ar","24000","-ac","1",str(fast)],check=True)
subprocess.run(["ffmpeg","-y","-v","error","-i",str(fast),"-b:a","160k",str(out/"dog_kore_125.mp3")],check=True)
with wave.open(str(fast),"rb") as f: duration=f.getnframes()/f.getframerate()
print("KORE_DOG_TTS_OK",json.dumps({"seconds":round(duration,2),"sentences":len(script)},ensure_ascii=False),flush=True)
if duration<25: raise RuntimeError("TTS_TOO_SHORT_OR_TRUNCATED")
