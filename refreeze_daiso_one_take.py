"""One-take Gemini Charon original voiceovers for two 생활알고리즘 Shorts.
Safety references: USDA FSIS for food; Asung Daiso statements quoted in Korean reporting 2025-2026.
"""
import os, wave, re, json, time
from pathlib import Path
from io import BytesIO
from google import genai
from google.genai import types
P=Path("out_new_two_shorts");P.mkdir(exist_ok=True)
SCRIPTS={
"refreeze":[
"냉동고기, 해동했다가 다시 얼리면 무조건 위험할까요? 정답은 해동 방법에 따라 달라집니다.",
"미국 농무부 USDA에 따르면, 냉장고에서 해동하고 차갑게 보관한 고기는 익히지 않고 다시 냉동해도 됩니다.",
"다만 해동과 재냉동을 반복하면 수분이 빠져 맛과 식감이 떨어질 수 있어요.",
"반대로 찬물이나 전자레인지로 해동했다면, 바로 충분히 익힌 뒤 냉동해야 합니다.",
"실온에 오래 둔 고기는 주의하세요. 두 시간 이상 방치했다면 다시 얼린다고 안전해지는 게 아닙니다.",
"처음부터 한 끼 분량씩 나눠 얼리면 더 편하고 안전하게 관리할 수 있죠. 도움 됐다면 구독과 좋아요! 생활알고리즘."
],
"daiso":[
"다이소에서 천 원짜리 물건을 볼 때마다 궁금하지 않으세요? 이렇게 싸게 팔아도 정말 이익이 남을까요?",
"비밀은 단순히 싸구려를 파는 게 아니라, 먼저 가격을 정하고 그에 맞게 상품을 만드는 유통 방식에 있어요.",
"다이소는 오백 원부터 오천 원까지, 정해진 여섯 가지 가격대로 상품을 판매합니다.",
"일반적으로는 원가에 이익을 더해 가격을 정하지만, 다이소는 정해 둔 가격을 맞추도록 상품의 구성과 포장, 사양을 조정합니다.",
"두 번째는 규모입니다. 전국 매장에서 판매할 물건을 대량으로 발주하면, 한 개당 매입 비용을 줄일 여지가 커집니다.",
"세 번째는 유통 단계예요. 협력업체와 직접 거래하는 직매입 구조로 중간 유통 비용을 낮춥니다.",
"또 불필요한 포장이나 부속품을 줄이고, 품질을 유지하면서 약속한 가격대에 맞추려고 하죠.",
"그렇다고 싼 물건이 항상 더 경제적인 건 아닙니다. 같은 가격이라도 용량, 크기, 내구성, 사용 횟수를 비교해야 해요.",
"결국 다이소가 저렴한 이유는 정해진 가격, 대량 발주, 비용을 줄이는 유통 구조가 함께 작동하기 때문입니다.",
"생활 속 궁금증, 오늘도 하나 해결! 도움이 됐다면 구독과 좋아요. 생활알고리즘!"
]}
c=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
for k,lines in SCRIPTS.items():
 text="\n".join(lines)
 r=c.models.generate_content(
   model="gemini-2.5-flash-preview-tts",
   contents="Read ALL paragraphs of this original Korean educational narration as ONE continuous performance with one stable consistent Charon male voice throughout. No timbre changes, music, or invented words. Clear friendly explainer, precise natural diction and finish all sentences. Brief pauses at paragraphs. Read exactly:\n\n"+text,
   config=types.GenerateContentConfig(response_modalities=["AUDIO"],speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
 part=next(p.inline_data for p in r.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data)
 raw=part.data
 mime=part.mime_type or ""
 if raw[:4]==b"RIFF":
  with wave.open(BytesIO(raw),"rb") as w: hz=w.getframerate();raw=w.readframes(w.getnframes())
 else:
  m=re.search(r"rate=(\d+)",mime);hz=int(m.group(1)) if m else 24000
 with wave.open(str(P/(k+"_one_take.wav")),"wb") as w:
  w.setnchannels(1);w.setsampwidth(2);w.setframerate(hz);w.writeframes(raw)
 (P/(k+"_script.json")).write_text(json.dumps(lines,ensure_ascii=False,indent=2),encoding="utf8")
 print("DONE",k,len(raw)/(hz*2),flush=True)
 time.sleep(21)
print("ALL_DONE",flush=True)
