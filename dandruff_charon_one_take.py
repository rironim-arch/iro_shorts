"""Generate ONE continuous Gemini Charon performance to prevent voice variations between independently generated segments.
Do not post to YouTube; quality review is required.
"""
from google import genai
from google.genai import types
from google.genai.errors import ClientError
from pathlib import Path
from io import BytesIO
import os,wave,re,json
OUT=Path("out_dandruff_one_take"); OUT.mkdir(exist_ok=True)
SENTENCES=[
"어깨에 하얀 비듬이 떨어진다면, 머리를 덜 감아서일까요? 비듬은 꼭 위생 문제는 아닙니다.",
"두피의 피지와 말라세지아 효모균, 건조함이나 헤어 제품 자극 등 여러 원인으로 각질이 늘어날 수 있어요.",
"비듬 샴푸를 고를 땐 광고보다 성분을 보세요. 케토코나졸이나 셀레늄 설파이드처럼 비듬 관리에 도움이 되는 성분이 있습니다.",
"살리실산은 들뜬 각질 제거에 도움을 줄 수 있어요. 한 가지 샴푸가 잘 안 맞으면 다른 성분을 시도할 수도 있습니다.",
"샴푸를 두피에 바른 뒤 제품 설명에 적힌 시간만큼 두고, 충분히 헹구세요. 너무 세게 긁으면 자극될 수 있어요.",
"사 주 정도 써도 낫지 않거나, 두피가 붉고 심하게 가렵다면 피부과 진료를 받으세요. 도움이 됐다면 구독과 좋아요! 생활알고리즘."
]
script="\n".join(SENTENCES)
c=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
r=c.models.generate_content(
 model="gemini-2.5-flash-preview-tts",
 contents="You are narrating ONE complete Korean educational YouTube Short in ONE continuous recording. Speak with the single same Korean male Charon voice throughout the ENTIRE script, no speaker changes, no changes in timbre, natural well-enunciated delivery, friendly factual tone, no extra words, no music. Brief natural pauses between paragraphs. Read every word exactly.\n\n"+script,
 config=types.GenerateContentConfig(
  response_modalities=["AUDIO"],
  speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
   prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
a=next(p.inline_data for p in r.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data)
data=a.data; mime=a.mime_type or ""
if data[:4]==b"RIFF":
 with wave.open(BytesIO(data),"rb") as w:
  rate=w.getframerate(); data=w.readframes(w.getnframes())
else:
 match=re.search(r"rate=(\d+)",mime)
 rate=int(match.group(1)) if match else 24000
with wave.open(str(OUT/"dandruff_charon_one_take.wav"),"wb") as w:
 w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(data)
(OUT/"script.json").write_text(json.dumps(SENTENCES,ensure_ascii=False,indent=2),encoding="utf8")
print("SINGLE_TAKE_SUCCESS",len(data)/(2*rate),flush=True)
