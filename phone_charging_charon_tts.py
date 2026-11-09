"""생활알고리즘: 휴대폰 충전/전자파 안전, six Charon takes, paid Gemini API project."""
import os, re, wave, time, json, sys
from pathlib import Path
from io import BytesIO
from google import genai
from google.genai import types

P=Path("out_phone_charging_charon"); P.mkdir(exist_ok=True)
LINES=[
  "휴대폰 충전하면서 베개 옆에 두고 주무시나요? 위험한 건 전자파일까요? 아니면 다른 이유일까요?",
  "휴대폰은 통신할 때 전자파를 내보냅니다. 하지만 현재까지 일반적인 휴대폰 전자파가 건강 문제를 일으킨다는 일관된 근거는 확인되지 않았습니다.",
  "그보다 주의할 건 충전 중 발열! 베개나 이불 아래 휴대폰을 두면 열이 빠져나가기 어려워 과열 위험이 커집니다.",
  "애플과 삼성도 이불이나 베개 밑 충전을 피하라고 안내합니다. 침대 위 대신 통풍이 잘되는 단단한 곳에서 충전하세요.",
  "케이블이 닳거나 손상됐다면 사용을 멈추고, 규격에 맞는 충전기를 쓰세요. 유난히 뜨거워지면 충전도 중단하세요.",
  "오늘의 핵심! 전자파 공포보다 충전 중 열 관리가 중요합니다. 도움이 됐다면 생활알고리즘 구독과 좋아요, 부탁드려요!"
]
c=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
saved=[]
for i,s in enumerate(LINES):
  f=P/f"scene_{i:02}.wav"
  if f.exists() and f.stat().st_size>4000:continue
  for attempt in range(4):
    try:
      r=c.models.generate_content(model="gemini-2.5-flash-preview-tts",
        contents=("Speak this Korean YouTube educational short narration exactly as written, friendly engaging male Charon voice, very clear articulation, medium natural pace, fully enunciate endings. No extra words.\n\n"+s),
        config=types.GenerateContentConfig(response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
      x=next(x.inline_data for x in r.candidates[0].content.parts if getattr(x,"inline_data",None) and x.inline_data.data)
      raw=x.data; mime=x.mime_type or ""
      if raw[:4]==b"RIFF":
        with wave.open(BytesIO(raw),"rb") as w:
          rate=w.getframerate(); raw=w.readframes(w.getnframes())
      else:
        m=re.search(r"rate=(\d+)",mime); rate=int(m.group(1)) if m else 24000
      with wave.open(str(f),"wb") as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(raw)
      print("SAVED",i,len(raw)/rate/2,flush=True)
      break
    except Exception as ex:
      print("RETRY",i,attempt,str(ex)[:450],flush=True)
      if attempt==3:sys.exit(2)
      time.sleep(45+attempt*30)
  time.sleep(21)
(P/"script.json").write_text(json.dumps(LINES,ensure_ascii=False,indent=2),encoding="utf8")
print("ALL SIX CHARON CLIPS SAVED",flush=True)
