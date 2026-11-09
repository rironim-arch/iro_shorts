import os,wave,time,re
from pathlib import Path
from io import BytesIO
from google import genai
from google.genai import types
dest=Path("out_caffeine_end");dest.mkdir(exist_ok=True)
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
s="오늘의 생활알고리즘! 도움이 됐다면 구독과 좋아요, 꼭 부탁드려요."
for attempt in range(3):
 try:
  r=client.models.generate_content(model="gemini-2.5-flash-preview-tts",contents="Read the following Korean narration VERBATIM, one male Charon speaker, warmly and clearly, no added speech: "+s,config=types.GenerateContentConfig(response_modalities=["AUDIO"],speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
  inline=next(p.inline_data for p in r.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data)
  raw=inline.data; mime=inline.mime_type or ""
  hz=int(re.search(r"rate=(\d+)",mime).group(1)) if re.search(r"rate=(\d+)",mime) else 24000
  with wave.open(str(dest/"scene_05.wav"),"wb") as f:
   f.setnchannels(1);f.setsampwidth(2);f.setframerate(hz);f.writeframes(raw)
  print("CHARON ENDING SAVED",len(raw),flush=True);break
 except Exception as exc:
  print("Attempt",attempt+1,str(exc)[:650],flush=True)
  if attempt==2:raise
  time.sleep(75)
