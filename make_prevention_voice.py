
"""One-off (manual user-requested) narration for hair prevention; no publishing."""
import os, re, wave, json
from pathlib import Path
from google import genai
from google.genai import types

req=json.loads(Path("hair_prevention_voice.json").read_text(encoding="utf-8"))
script=" ".join(req["sentences"])
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
response=client.models.generate_content(
    model="gemini-2.5-flash-preview-tts",
    contents=("Read the following Korean informational YouTube Shorts narration, "
              "in a clear and compelling natural adult Korean male voice. "
              "Slightly energetic, conversational, no additional words, moderate pace.\n\n"+script),
    config=types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")
            )
        )
    )
)
if not response.candidates: raise RuntimeError("TTS no candidates")
audio=next(p.inline_data for p in response.candidates[0].content.parts if getattr(p, "inline_data", None))
raw=audio.data
mime=(audio.mime_type or "").lower()
if not raw: raise RuntimeError("TTS empty audio")
if "wav" in mime or raw[:4] == b"RIFF":
    Path("hair_prevention_voice.wav").write_bytes(raw)
elif "pcm" in mime or "audio/l16" in mime or not mime:
    m=re.search(r"rate=(\d+)",mime)
    rate=int(m.group(1)) if m else 24000
    with wave.open("hair_prevention_voice.wav","wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(raw)
else:
    raise RuntimeError("Unsupported output audio: "+mime)
print("Generated audio.")
