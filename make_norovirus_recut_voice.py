"""Produce separate Gemini Charon TTS chunks for exact scene-level sync; never upload to YouTube."""
import json, os, re, time, wave
from pathlib import Path
from google import genai
from google.genai import types
req=json.loads(Path("norovirus_recut_script.json").read_text(encoding="utf-8"))
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
Path("norovirus_recut_audio").mkdir(exist_ok=True)
for i,chunk in enumerate(req["chunks"]):
 prompt=("You are an excellent mature Korean male narrator for an informative short documentary. "
 "Read ONLY the sentence below, no preface, no extra words, no music. "
 "Clear Korean diction, warm neutral male tone, consistent voice, natural documentary delivery, moderately quick pace. "
 "If you see the letters CDC, pronounce them as the three English letter names, C D C (not the Korean transliteration). "
 "Do not add words, do not repeat yourself. Sentence to narrate:\n"+chunk["say"])
 for attempt in range(3):
  try:
   r=client.models.generate_content(model="gemini-2.5-flash-preview-tts",
    contents=prompt,config=types.GenerateContentConfig(response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
   part=next(p.inline_data for p in r.candidates[0].content.parts if getattr(p,"inline_data",None))
   raw=part.data;mime=(part.mime_type or "").lower();path=Path("norovirus_recut_audio")/f"scene_{i:02d}.wav"
   if raw[:4]==b"RIFF" or "wav" in mime: path.write_bytes(raw)
   else:
    m=re.search(r"rate=(\\d+)",mime)
    rate=int(m.group(1)) if m else 24000
    with wave.open(str(path),"wb") as f:
     f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes(raw)
   print("Generated chunk",i, "size",len(raw),flush=True)
   break
  except Exception as e:
   if attempt==2:raise
   print("Retry chunk",i,type(e).__name__,str(e)[:150],flush=True);time.sleep(12)
 time.sleep(6)
print("Ready:",len(req["chunks"]),"audio chunks")
