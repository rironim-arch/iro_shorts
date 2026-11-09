"""생활알고리즘: 두피 비듬의 원인과 관리 — original educational Charon voiceover.
Sources: AAD, NHS, Mayo Clinic (manual review required before posting).
"""
import os,time,re,json,wave
from pathlib import Path
from io import BytesIO
from google import genai
from google.genai import types
from google.genai.errors import ClientError
P=Path("out_dandruff_charon"); P.mkdir(exist_ok=True)
LINES=[
"어깨에 하얀 비듬이 떨어진다면, 머리를 덜 감아서일까요? 비듬은 꼭 위생 문제는 아닙니다.",
"두피의 피지와 말라세지아 효모균, 건조함이나 헤어 제품 자극 등 여러 원인으로 각질이 늘어날 수 있어요.",
"비듬 샴푸를 고를 땐 광고보다 성분을 보세요. 케토코나졸이나 셀레늄 설파이드처럼 비듬 관리에 도움이 되는 성분이 있습니다.",
"살리실산은 들뜬 각질 제거에 도움을 줄 수 있어요. 한 가지 샴푸가 잘 안 맞으면 다른 성분을 시도할 수도 있습니다.",
"샴푸를 두피에 바른 뒤 제품 설명에 적힌 시간만큼 두고, 충분히 헹구세요. 너무 세게 긁으면 자극될 수 있어요.",
"사 주 정도 써도 낫지 않거나, 두피가 붉고 심하게 가렵다면 피부과 진료를 받으세요. 도움이 됐다면 구독과 좋아요! 생활알고리즘."
]
(P/"script.json").write_text(json.dumps(LINES,ensure_ascii=False,indent=2),encoding="utf-8")
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
out=[]
for i,text in enumerate(LINES):
 for attempt in range(4):
  try:
   r=client.models.generate_content(model="gemini-2.5-flash-preview-tts",
     contents="Korean educational video. Read EXACTLY this Korean script in a natural, friendly, authoritative male voice, no added words. Moderate pace, crisp enunciation including ALL sentence endings, clear breaths and pauses:\n"+text,
     config=types.GenerateContentConfig(response_modalities=["AUDIO"],speech_config=types.SpeechConfig(
       voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
   audio=next(p.inline_data for p in r.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data)
   raw=audio.data; mime=audio.mime_type or ""
   if raw[:4]==b"RIFF":
    with wave.open(BytesIO(raw),"rb") as w:
     hz=w.getframerate(); raw=w.readframes(w.getnframes())
   else:
    m=re.search(r"rate=(\d+)",mime);hz=int(m.group(1)) if m else 24000
   filename=P/f"scene_{i:02}.wav"
   with wave.open(str(filename),"wb") as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(hz);w.writeframes(raw)
   d=round(len(raw)/(hz*2),3);out.append({"scene":i,"duration":d,"text":text})
   (P/"report.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
   print("SAVED",i,d,flush=True)
   break
  except ClientError as e:
   print("RATE/ERROR",i,attempt+1,str(e)[:300],flush=True)
   if attempt==3:raise
   time.sleep(70)
 time.sleep(23)
print("DANDRUFF CHARON COMPLETE",flush=True)
