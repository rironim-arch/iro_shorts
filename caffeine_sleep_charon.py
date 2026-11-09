"""Narration for original 생활알고리즘 caffeine/sleep Short; Gemini Charon.
Produces WAV + metadata, never uploads to YouTube.
"""
import os, re, time, wave, json, traceback
from pathlib import Path
from io import BytesIO
from google import genai
from google.genai import types

OUT=Path("out_caffeine_charon"); OUT.mkdir(exist_ok=True)
LINES=[
 "저녁에 커피 한 잔 마셨는데, 왜 새벽까지 잠이 안 올까요? 카페인이 뇌의 졸음 신호를 가리기 때문입니다.",
 "우리가 깨어 있는 동안 뇌에는 아데노신이 쌓여요. 이 물질은 이제 쉴 시간이라고 알려주는 신호죠.",
 "그런데 카페인이 아데노신의 작용을 막습니다. 피로가 사라진 게 아니라, 졸음을 덜 느끼는 거예요.",
 "더 중요한 건 지속 시간! 카페인은 보통 다섯에서 여섯 시간이 지나도, 몸에 절반 정도 남을 수 있어요.",
 "그래서 늦은 오후 커피도 밤잠을 방해할 수 있습니다. 잠을 설치면 잠들기 최소 여섯 시간 전엔 카페인을 피하고, 민감하면 더 일찍 끊어보세요.",
 "오늘의 생활알고리즘! 도움이 됐다면 구독과 좋아요, 꼭 부탁드려요."
]
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
report=[]
for i,text in enumerate(LINES):
    print("START",i,flush=True)
    try:
      r=client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents="Read the following Korean narration VERBATIM in a friendly, energetic, clear male voice for a factual YouTube Short. Medium pace, articulate all Korean syllables, natural pauses. No extra speech.\n\n"+text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
      inline=next(p.inline_data for p in r.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data)
      raw=inline.data
      mime=inline.mime_type or ""
      if raw[:4]==b"RIFF":
         with wave.open(BytesIO(raw),"rb") as w:
            hz=w.getframerate(); ch=w.getnchannels(); sw=w.getsampwidth(); pcm=w.readframes(w.getnframes())
      else:
         m=re.search(r"rate=(\\d+)",mime)
         hz=int(m.group(1)) if m else 24000; ch=1; sw=2; pcm=raw
      if ch!=1 or sw!=2: raise RuntimeError("unexpected audio encoding")
      with wave.open(str(OUT/f"scene_{i:02}.wav"),"wb") as w:
         w.setnchannels(1);w.setsampwidth(2);w.setframerate(hz);w.writeframes(pcm)
      report.append({"index":i,"text":text,"seconds":len(pcm)/hz/2,"rate":hz})
      (OUT/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
      print("SAVED",i,round(report[-1]["seconds"],2),flush=True)
      if i<len(LINES)-1:time.sleep(3)
    except Exception as e:
      print("ERROR",i,type(e).__name__,str(e)[:1000],flush=True)
      raise
(OUT/"script.txt").write_text("\n".join(LINES),encoding="utf8")
print("ALL COMPLETE",flush=True)
