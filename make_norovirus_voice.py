"""Generate one approved norovirus short Korean male voice with Gemini. No upload to YouTube."""
import json, os, re, wave
from pathlib import Path
from google import genai
from google.genai import types

request=json.loads(Path("norovirus_short_request.json").read_text(encoding="utf-8"))
spoken=" ".join(request["sentences"])
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
prompt=("Read this Korean health-education narration naturally and EXACTLY as written, with no additions or omitted words. "
"Warm, trustworthy adult Korean male narrator, engaging documentary storytelling, articulate and deliberate but never theatrical. "
"Short breathing pauses at sentence boundaries and at transitions between sections. "
"Pronounce CDC as 씨디씨. Use natural Korean pronunciation for norovirus, 20 seconds and 48 hours.\n\n"+spoken)
r=client.models.generate_content(
 model="gemini-2.5-flash-preview-tts",contents=prompt,
 config=types.GenerateContentConfig(response_modalities=["AUDIO"],
 speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
 prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
if not r.candidates: raise RuntimeError("Gemini TTS returned no candidate")
parts=r.candidates[0].content.parts
a=next((p.inline_data for p in parts if getattr(p,"inline_data",None)),None)
if a is None or not a.data: raise RuntimeError("Gemini TTS returned no audio data")
raw=a.data; mime=(a.mime_type or "").lower()
if raw[:4]==b"RIFF" or "wav" in mime:
 Path("norovirus_voice.wav").write_bytes(raw)
elif "pcm" in mime or "audio/l16" in mime or not mime:
 m=re.search(r"rate=(\d+)",mime)
 rate=int(m.group(1)) if m else 24000
 with wave.open("norovirus_voice.wav","wb") as f:
  f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes(raw)
else: raise RuntimeError("Unsupported audio type: "+mime)
Path("norovirus_script.txt").write_text(request["title"]+"\n\n"+"\n".join(request["sentences"])+"\n",encoding="utf-8")
print("Created Gemini Korean male narration WAV.")
