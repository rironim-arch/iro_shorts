"""Create scene-level Gemini narration for a short video; does not publish online."""
import json, os, re, time, wave
from pathlib import Path
from google import genai
from google.genai import types

req=json.loads(Path("microwave_short_request.json").read_text(encoding="utf-8"))
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
Path("microwave_audio").mkdir(exist_ok=True)
for i,chunk in enumerate(req["chunks"]):
 prompt=("Read the following Korean narration exactly. Natural articulate Korean adult male narrator; Charon warm documentary tone. "
         "No extra words, no music, no opening or closing. Speak at a consistent clear moderate pace. "
         "Say 'PP' as English letters P P, say 'USDA' as English letters U S D A. "
         "TEXT TO READ:\n" + chunk["say"])
 for attempt in range(3):
  try:
   r=client.models.generate_content(model="gemini-2.5-flash-preview-tts", contents=prompt,
       config=types.GenerateContentConfig(response_modalities=["AUDIO"],speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
   part=next(p.inline_data for p in r.candidates[0].content.parts if getattr(p,"inline_data",None))
   raw=part.data; mime=(part.mime_type or "").lower()
   path=Path("microwave_audio")/f"scene_{i:02d}.wav"
   if raw[:4] == b"RIFF" or "wav" in mime:
    path.write_bytes(raw)
   else:
    m=re.search(r"rate=(\\d+)",mime)
    rate=int(m.group(1)) if m else 24000
    with wave.open(str(path),"wb") as f:
     f.setnchannels(1); f.setsampwidth(2); f.setframerate(rate); f.writeframes(raw)
   print("scene",i,"bytes",len(raw),flush=True)
   break
  except Exception as e:
   if attempt==2: raise
   print("Retry",i,str(e)[:160],flush=True); time.sleep(8)
 time.sleep(4)
print("Done",len(req["chunks"]))
