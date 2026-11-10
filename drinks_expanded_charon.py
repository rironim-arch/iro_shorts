"""Living Algorithm: cola versus grape juice, coffee frappuccino, milk tea, and pearl shake.
Verified 2026-11-10: SSG Coca Cola 44 kcal/100ml; Dure Coop pure grape 53 kcal/100ml;
Starbucks Java Chip Frappuccino Tall 285 kcal/355ml; GongCha Brown Sugar Signature Milk Tea + Pearl L 424 kcal/473ml;
GongCha Black Milk Tea Pearl Shake L 605 kcal/473ml. Product-specific examples, no universal claim.
"""
from pathlib import Path
from io import BytesIO
from google import genai
from google.genai import types
import os, wave, re, json
out=Path("out_drinks_expanded");out.mkdir(exist_ok=True)
lines=[
"콜라만 안 마시면 살이 덜 찔까요? 사실 콜라보다 열량이 높은 음료가 의외로 많습니다. 같은 양으로 비교해 볼게요.",
"기준은 백 밀리리터! 일반 콜라는 약 사십사 킬로칼로리입니다.",
"그런데 백 퍼센트 포도주스 중에는 백 밀리리터에 오십삼 킬로칼로리인 제품도 있습니다. 설탕을 따로 넣지 않아도 과일 당은 들어 있어요.",
"달콤한 커피는 어떨까요? 자바 칩 프라푸치노 톨은 삼백오십오 밀리리터에 이백팔십오 킬로칼로리. 백 밀리리터 기준 약 팔십 킬로칼로리입니다.",
"흑당 밀크티 펄 라지는 한 잔에 사백이십사 킬로칼로리! 같은 백 밀리리터로 환산하면 약 구십 킬로칼로리죠.",
"블랙 밀크티 펄 셰이크 라지는 한 잔에 무려 육백오 킬로칼로리. 백 밀리리터당 약 백이십팔 킬로칼로리입니다.",
"단, 이건 특정 제품들의 영양정보예요. 같은 종류라도 크기와 레시피에 따라 크게 달라집니다.",
"그리고 칼로리가 높다고 한 번 마시면 무조건 살이 찌는 건 아닙니다. 하루 전체 섭취 열량과 마시는 빈도가 더 중요해요.",
"음료를 고를 땐 이름보다 영양표시를 보세요. 총열량, 용량, 당류를 함께 확인하면 도움이 됩니다.",
"몰랐던 생활정보, 오늘도 하나 해결! 생활알고리즘, 구독과 좋아요 부탁드립니다."
]
(out/"script.json").write_text(json.dumps(lines,ensure_ascii=False,indent=2),encoding="utf8")
r=genai.Client(api_key=os.environ["GEMINI_API_KEY"]).models.generate_content(
 model="gemini-2.5-flash-preview-tts",
 contents="Record the ENTIRE following Korean narration as ONE continuous take in the same consistent friendly Korean male Charon voice. This is clear, credible, energetic original nutrition reporting. No voice changes, no speakers other than the single narrator. Speak every Korean word and every sentence ending without skipping. Add slight natural pauses between paragraphs. No song, no invented words. Read EXACTLY:\n\n"+"\n\n".join(lines),
 config=types.GenerateContentConfig(response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
part=next(p.inline_data for p in r.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data)
raw=part.data; mime=part.mime_type or ""
if raw[:4]==b"RIFF":
 with wave.open(BytesIO(raw),"rb") as w: rate=w.getframerate(); n=w.getnchannels();width=w.getsampwidth();raw=w.readframes(w.getnframes())
else:
 m=re.search(r"rate=(\\d+)",mime);rate=int(m.group(1)) if m else 24000;n=1;width=2
with wave.open(str(out/"expanded_drinks_charon_one_take.wav"),"wb") as w:
 w.setnchannels(n);w.setsampwidth(width);w.setframerate(rate);w.writeframes(raw)
print("SUCCESS",rate,n,width,"DURATION_S",round(len(raw)/rate/n/width,2),flush=True)
