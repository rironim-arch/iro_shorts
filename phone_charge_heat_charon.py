"""Original 생활알고리즘 Shorts: phone charging under pillow.
Google Gemini 2.5 Flash TTS / Charon, coherent six-part narration.
No YouTube upload; generated parts for human editorial review.
"""
import os, re, json, time, wave
from pathlib import Path
from io import BytesIO
from google import genai
from google.genai import types
from google.genai.errors import ClientError
OUT=Path("out_phone_heat_charon");OUT.mkdir(exist_ok=True)
LINES=[
"잠들기 전, 휴대폰을 베개 옆에 놓고 충전하시나요? 전자파보다 먼저 확인할 위험이 있습니다.",
"휴대폰은 통신할 때 전파를 내보내지만, 현재 과학적 근거로는 일반적인 휴대폰 전파가 건강 문제를 일으킨다고 확립되지 않았습니다.",
"그런데 충전할 때는 휴대폰과 충전기에 열이 생길 수 있어요. 이불이나 베개 아래는 열이 잘 빠져나가지 않습니다.",
"열이 갇히면 과열 위험이 커집니다. 특히 케이블이나 충전기가 손상됐다면 위험이 더 커질 수 있어요.",
"충전할 때는 침대나 베개 밑이 아니라, 통풍되는 단단한 곳에 두세요. 너무 뜨거워지면 충전을 멈추고 식혀 주세요.",
"오늘 밤, 충전 위치부터 바꿔보세요. 도움이 됐다면 구독과 좋아요! 생활알고리즘."
]
(OUT/"script.json").write_text(json.dumps(LINES,ensure_ascii=False,indent=2),encoding="utf8")
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
done=[]
for i,s in enumerate(LINES):
 for attempt in range(4):
  try:
   r=client.models.generate_content(
     model="gemini-2.5-flash-preview-tts",
     contents="You are a clear friendly Korean male educational Shorts narrator. Speak ONLY the following Korean script VERBATIM. No added words, no skipped words. Articulate word endings; natural explanatory pacing and confident, engaging tone. No ambient sound.\n\n"+s,
     config=types.GenerateContentConfig(response_modalities=["AUDIO"],
       speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
         prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
   part=next(p.inline_data for p in r.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data)
   raw=part.data;mime=part.mime_type or ""
   if raw[:4]==b"RIFF":
    with wave.open(BytesIO(raw),"rb") as wf:
     rate=wf.getframerate(); nch=wf.getnchannels(); width=wf.getsampwidth(); pcm=wf.readframes(wf.getnframes())
   else:
    m=re.search(r"rate=(\d+)",mime)
    rate=int(m.group(1)) if m else 24000
    nch=1;width=2;pcm=raw
   if nch!=1 or width!=2:raise ValueError("Unrecognized PCM encoding")
   with wave.open(str(OUT/f"scene_{i:02d}.wav"),"wb") as wf:
    wf.setnchannels(1);wf.setsampwidth(2);wf.setframerate(rate);wf.writeframes(pcm)
   done.append({"scene":i,"text":s,"seconds":round(len(pcm)/(2*rate),2)})
   (OUT/"report.json").write_text(json.dumps(done,ensure_ascii=False,indent=2),encoding="utf8")
   print("SAVED",i,done[-1]["seconds"],flush=True)
   break
  except ClientError as e:
   print("API ERROR",i,attempt+1,str(e)[:350],flush=True)
   if attempt==3:raise
   time.sleep(72)
  except Exception:
   raise
 time.sleep(19)
