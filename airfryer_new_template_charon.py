"""생활알고리즘 new dynamic visual template: original air fryer safety video, one Charon performance."""
from pathlib import Path
from io import BytesIO
import os, re, wave, json
from google import genai
from google.genai import types
O=Path("out_airfryer_template_charon")
O.mkdir(exist_ok=True)
LINES=[
"에어프라이어에 종이호일만 넣고 예열하시나요? 이건 불이 날 수도 있는 행동입니다.",
"종이호일이 가벼우면 뜨거운 바람에 들려 위쪽 열선에 닿을 수 있기 때문이죠.",
"필립스는 일부 모델에서 종이호일 사용을 권장하지 않습니다. 공기 흐름을 막아 조리 성능까지 떨어질 수 있어요.",
"종이호일을 쓰기 전에는 기기 설명서를 먼저 확인하세요. 사용이 허용된 제품이라면 음식으로 종이를 눌러 고정해야 합니다.",
"예열할 때 종이만 넣는 건 피하세요. 오늘도 안전한 생활 습관! 생활알고리즘, 구독과 좋아요 부탁드립니다."
]
(O/"script.json").write_text(json.dumps(LINES, ensure_ascii=False, indent=2), encoding="utf-8")
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
r=client.models.generate_content(
 model="gemini-2.5-flash-preview-tts",
 contents="Read the complete Korean script as ONE continuous Charon Korean male narrator in natural, crisp, engaging educational voice. The first sentence should be urgent but not exaggerated. Keep identical voice and timbre until the end, and pronounce every sentence ending and CTA, without music or any extra text. Give natural small pauses between paragraphs.\n\n"+"\n\n".join(LINES),
 config=types.GenerateContentConfig(response_modalities=["AUDIO"],speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon"))))
)
a=next(p.inline_data for p in r.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data)
raw=a.data; mime=a.mime_type or ""
if raw[:4]==b"RIFF":
 with wave.open(BytesIO(raw),"rb") as f: rate=f.getframerate(); chans=f.getnchannels(); width=f.getsampwidth(); raw=f.readframes(f.getnframes())
else:
 m=re.search(r"rate=(\\d+)",mime); rate=int(m.group(1)) if m else 24000; chans=1;width=2
with wave.open(str(O/"airfryer_single_charon.wav"),"wb") as f:
 f.setnchannels(chans);f.setsampwidth(width);f.setframerate(rate);f.writeframes(raw)
print("COMPLETE",round(len(raw)/rate/chans/width,3),flush=True)
