"""Generate one continuous original lifestyle educational Shorts narration. Paid Gemini API, Charon only."""
from google import genai
from google.genai import types
from pathlib import Path
from io import BytesIO
import os, wave, re, json
OUT=Path("out_juice_short_charon")
OUT.mkdir(exist_ok=True)
PARAGRAPHS=[
"콜라보다 칼로리가 높은 음료? 의외로 건강하다고 생각했던 과일주스일 수 있습니다. 같은 양으로 비교해 볼까요?",
"국내 코카콜라는 백 밀리리터에 약 사십사 킬로칼로리. 반면 백 퍼센트 포도주스의 한 제품은 약 쉰여덟 킬로칼로리입니다.",
"같은 용량인데 포도주스가 약 삼십 퍼센트 높은 거죠. 설탕 무첨가라고 적혀 있어도 과일 자체의 당분은 남아 있습니다.",
"그렇다고 모든 과일주스가 콜라보다 칼로리가 높은 건 아닙니다. 오렌지주스는 비슷한 제품도 있고, 브랜드와 용량에 따라 달라요.",
"특히 주스는 통과일보다 식이섬유가 적어 포만감이 덜할 수 있습니다. 건강을 생각해 마셔도 많이 마시면 하루 총 섭취 열량이 늘 수 있어요.",
"영국 NHS는 과일주스와 스무디를 합해 하루 백오십 밀리리터 이하를 권장합니다. 제품의 총 열량과 당류를 비교하고, 가능하면 통과일을 선택해 보세요.",
"건강해 보이는 음료도 양을 확인하는 습관이 중요합니다. 도움 됐다면 구독과 좋아요! 생활알고리즘."
]
(OUT/"paragraphs.json").write_text(json.dumps(PARAGRAPHS,ensure_ascii=False,indent=2),encoding="utf8")
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
resp=client.models.generate_content(
  model="gemini-2.5-flash-preview-tts",
  contents="Read the COMPLETE Korean script below exactly ONCE as ONE consistent and engaging friendly male narrator (Charon voice). Be calm and credible. Keep the same voice and tone all the way through; moderate speech pace; separate paragraphs with a little pause, and articulate every final word including the subscribe and like sentence. No additions, no musical notes, no speaker labels.\n\n"+"\n\n".join(PARAGRAPHS),
  config=types.GenerateContentConfig(response_modalities=["AUDIO"],speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
part=next(p.inline_data for p in resp.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data)
raw=part.data; mime=part.mime_type or ""
if raw[:4]==b"RIFF":
 with wave.open(BytesIO(raw),"rb") as f:
  sr=f.getframerate();channels=f.getnchannels(); width=f.getsampwidth();raw=f.readframes(f.getnframes())
else:
 match=re.search(r"rate=(\\d+)",mime);sr=int(match.group(1)) if match else 24000;channels=1;width=2
with wave.open(str(OUT/"juice_charon_one_take.wav"),"wb") as w:
 w.setnchannels(channels);w.setsampwidth(width);w.setframerate(sr);w.writeframes(raw)
print("ONE_TAKE_SUCCESS", round(len(raw)/(sr*channels*width),3), "rate",sr,flush=True)
