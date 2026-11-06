"""One-off approved 생활알고리즘 hair-loss medicine narration; Gemini voice only."""
import json, os, re, wave
from pathlib import Path
from google import genai
from google.genai import types

request = json.loads(Path("hairloss_drug_request.json").read_text(encoding="utf-8"))
sentences = request["sentences"]
script = " ".join(sentences)
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
prompt = (
    "Speak the Korean script EXACTLY as written, with no additions, no omissions, "
    "and no reading out stage directions. Natural adult Korean male voice, clear and "
    "credible medical-information presenter, confident but not alarming. "
    "Warm moderately brisk delivery, short natural pause at each full stop. "
    "Accurate pronunciation of medicine names and doses.\n\n" + script
)
response = client.models.generate_content(
    model=os.getenv("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts"),
    contents=prompt,
    config=types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")
            )
        ),
    ),
)
if not response.candidates:
    raise RuntimeError("Gemini returned no candidates")
parts = response.candidates[0].content.parts
payloads = [p.inline_data for p in parts if getattr(p, "inline_data", None)]
if not payloads:
    raise RuntimeError("Gemini returned no audio")
audio = payloads[0]
raw = audio.data
mime = (audio.mime_type or "").lower()
if not raw:
    raise RuntimeError("Gemini returned empty audio")
out = Path("hairloss_drug_voice.wav")
if "wav" in mime or raw[:4] == b"RIFF":
    out.write_bytes(raw)
elif "pcm" in mime or "audio/l16" in mime or not mime:
    m = re.search(r"rate=(\\d+)", mime)
    rate = int(m.group(1)) if m else 24000
    with wave.open(str(out), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(raw)
else:
    raise RuntimeError("Unsupported Gemini audio MIME type: " + mime)
Path("hairloss_drug_script.txt").write_text(
    request["title"] + "\n\n" + "\n".join(sentences) + "\n",
    encoding="utf-8",
)
print(f"Gemini Korean narration created: {out} ({out.stat().st_size} bytes)")
