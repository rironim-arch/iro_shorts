"""Humidifier white dust: source-checked, single-take Charon voice for new 생활알고리즘 visual template.
Source: US EPA Use and Care of Home Humidifiers (2022); CDC Preventing Waterborne Germs at Home.
"""
from pathlib import Path
from io import BytesIO
from google import genai
from google.genai import types
import os, wave, re, json
O=Path("out_humidifier_template"); O.mkdir(exist_ok=True)
LINES=[
"가습기 옆 가구에 하얀 가루가 쌓였나요? 먼지가 아닐 수도 있습니다!",
"특히 초음파식 가습기는 물속 미네랄을 미세한 물방울과 함께 공기 중으로 내보낼 수 있어요.",
"미국 환경보호청 EPA는 이런 입자가 가구에 하얀 먼지처럼 남을 수 있다고 설명합니다.",
"이런 현상이 나타나면 제품 설명서를 확인하고, 허용되는 경우 증류수처럼 미네랄이 적은 물을 사용해 보세요.",
"물만 바꾼다고 끝은 아니에요. 물통은 매일 비우고 말려 새 물을 채우고, 기기 설명서대로 정기적으로 세척해야 합니다.",
"하얀 가루가 생긴다면 가습기의 물과 관리법부터 확인하세요. 도움이 됐다면 생활알고리즘 구독과 좋아요!"
]
(O/"script.json").write_text(json.dumps(LINES,ensure_ascii=False,indent=2),encoding="utf8")
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
r=client.models.generate_content(
 model="gemini-2.5-flash-preview-tts",
 contents="Read this entire original Korean educational YouTube Short as ONE continuous performance using ONE stable Charon male voice, highly energetic clear strong first 2 seconds, then warm direct conversational narration, accurate numbers, no other speaker/timbre changes, no music, no extra words, brief pauses between paragraphs, read exactly every last syllable.\n\n"+"\n\n".join(LINES),
 config=types.GenerateContentConfig(response_modalities=["AUDIO"],speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
a=next(p.inline_data for p in r.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data)
raw=a.data;mime=a.mime_type or ""
if raw[:4]==b"RIFF":
 with wave.open(BytesIO(raw),"rb") as w:
  rate=w.getframerate();ch=w.getnchannels();width=w.getsampwidth();raw=w.readframes(w.getnframes())
else:
 m=re.search(r"rate=(\\d+)",mime);rate=int(m.group(1)) if m else 24000;ch=1;width=2
with wave.open(str(O/"humidifier_charon_one_take.wav"),"wb") as w:
 w.setnchannels(ch);w.setsampwidth(width);w.setframerate(rate);w.writeframes(raw)
print("VOICE_SUCCESS seconds",round(len(raw)/rate/ch/width,2),flush=True)
