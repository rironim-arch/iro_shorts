"""Original 생활알고리즘 Shorts: toilet urine splashback and hygiene, Gemini Charon only.
Research: J-Stage 2017 fluorescent study; PNAS Nexus 2025 fluid dynamics; CDC clean hands.
"""
import os,time,re,json,wave
from pathlib import Path
from io import BytesIO
from google import genai
from google.genai import types
from google.genai.errors import ClientError
P=Path("out_toilet_charon");P.mkdir(exist_ok=True)
LINES=[
"양변기에 서서 소변 볼 때, 눈에 안 보이는 물방울은 어디까지 튈까요? 생각보다 주변에 튈 수 있습니다.",
"소변 줄기가 변기 안 물이나 단단한 면에 부딪히면 작은 물방울이 튀어 나옵니다. 변기 모양과 닿는 각도도 영향을 줍니다.",
"형광 물질로 비교한 한 실험에서는 서서 소변 볼 때 주변 튐이 관찰됐지만, 앉은 자세에서는 관찰되지 않았습니다.",
"그래서 집에서는 앉아서 소변을 보면 주변 튐을 줄이는 데 도움이 될 수 있어요. 다만 모든 변기에서 완전히 없어지는 건 아닙니다.",
"변기 가장자리와 바닥에 묻은 물방울은 정기적으로 닦아 주세요. 사용 후에는 비누로 손을 적어도 이십 초 씻는 게 중요합니다.",
"오늘의 생활알고리즘! 깨끗한 화장실은 작은 습관부터 시작돼요. 도움이 됐다면 구독과 좋아요, 부탁드려요!"
]
(P/"script.json").write_text(json.dumps(LINES,ensure_ascii=False,indent=2),encoding="utf8")
c=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
report=[]
for i,s in enumerate(LINES):
 for attempt in range(4):
  try:
   r=c.models.generate_content(model="gemini-2.5-flash-preview-tts",
       contents="Narrate this exact Korean YouTube Shorts educational narration in clear, engaging, warm Charon male voice, with all Korean syllables and sentence endings intact, natural pace, no added words or music:\n"+s,
       config=types.GenerateContentConfig(response_modalities=["AUDIO"],speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
   a=next(p.inline_data for p in r.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data)
   raw=a.data; mime=a.mime_type or ""
   if raw[:4]==b"RIFF":
    with wave.open(BytesIO(raw),"rb") as w: rate=w.getframerate();raw=w.readframes(w.getnframes())
   else:
    m=re.search(r"rate=(\d+)",mime);rate=int(m.group(1)) if m else 24000
   with wave.open(str(P/f"scene_{i:02}.wav"),"wb") as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(raw)
   d=round(len(raw)/rate/2,2);report.append({"scene":i,"seconds":d,"text":s})
   (P/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
   print("SAVED",i,d,flush=True)
   break
  except ClientError as ex:
   print("ERROR",i,attempt+1,str(ex)[:400],flush=True)
   if attempt==3:raise
   time.sleep(73)
 time.sleep(22)
print("SUCCESS ALL SIX",flush=True)
