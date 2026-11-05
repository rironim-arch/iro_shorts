"""Generate Korean narrator WAV once; no YouTube upload, no recurring schedule."""
import json, os, re, wave
from pathlib import Path
from google import genai
from google.genai import types
request=json.loads(Path("voice_request.json").read_text(encoding="utf-8"))
sentences=request["sentences"]
script=" ".join(sentences)
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
prompt=("Read the following Korean informative YouTube narration in a clear, confident, "
 "friendly, natural adult Korean male voice. Moderate conversational pace, small pauses "
 "between sentences, no added words, accurate pronunciation.\n\n"+script)
response=client.models.generate_content(
 model="gemini-2.5-flash-preview-tts",contents=prompt,
 config=types.GenerateContentConfig(response_modalities=["AUDIO"],
 speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
 prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
parts=response.candidates[0].content.parts
audio=next(p.inline_data for p in parts if getattr(p,"inline_data",None))
raw=audio.data
mime=(audio.mime_type or "").lower()
if not raw: raise RuntimeError("No TTS audio returned")
if "wav" in mime or raw[:4]==b"RIFF":
 Path("hairloss_voice.wav").write_bytes(raw)
elif "pcm" in mime or "audio/l16" in mime or not mime:
 match=re.search(r"rate=(\d+)",mime)
 rate=int(match.group(1)) if match else 24000
 with wave.open("hairloss_voice.wav","wb") as wav:
  wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(rate);wav.writeframes(raw)
else:
 raise RuntimeError("Unrecognized TTS audio type: "+mime)
Path("script_copy.json").write_text(json.dumps(request,ensure_ascii=False),encoding="utf-8")
print("WAV audio generated.")
