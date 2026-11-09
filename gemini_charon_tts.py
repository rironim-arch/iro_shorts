"""Gemini 2.5 Flash TTS, Charon voice, for manually-reviewed Shorts only.

Set GEMINI_API_KEY as a GitHub Actions repository secret.
No API keys are stored in source control and this module never uploads videos.
"""
import asyncio
import os
import re
import wave
from pathlib import Path

from google import genai
from google.genai import types

MODEL = "gemini-2.5-flash-preview-tts"
VOICE = "Charon"

def _generate(text: str, destination: Path) -> None:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("Missing GEMINI_API_KEY GitHub Actions secret. Never commit your API key.")
    client = genai.Client(api_key=key)
    response = client.models.generate_content(
        model=MODEL,
        contents=(
            "Speak ONLY the following Korean YouTube Shorts narration. "
            "Voice: natural, friendly, clear Korean male news-presenter style. "
            "Keep every word and the final subscription/like reminder. "
            "Articulate endings and pause naturally; do not introduce yourself.\n\n"
            + text
        ),
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=VOICE)
                )
            ),
        ),
    )
    candidates = getattr(response, "candidates", None) or []
    if not candidates or not getattr(candidates[0], "content", None):
        raise RuntimeError("Gemini did not return an audio candidate; verify quota and model access.")
    parts = getattr(candidates[0].content, "parts", None) or []
    inline = next(
        (p.inline_data for p in parts
         if getattr(p, "inline_data", None) and p.inline_data.data),
        None,
    )
    if inline is None:
        raise RuntimeError("Gemini TTS returned no audio data.")
    raw = inline.data
    mime = (inline.mime_type or "").lower()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if raw.startswith(b"RIFF"):
        destination.write_bytes(raw)
    else:
        if mime and "pcm" not in mime and "l16" not in mime:
            raise RuntimeError("Unexpected TTS encoding: " + mime)
        if len(raw) % 2:
            raise RuntimeError("Unexpected odd length for 16-bit PCM output.")
        match = re.search(r"rate=(\d+)", mime)
        sample_rate = int(match.group(1)) if match else 24000
        with wave.open(str(destination), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(raw)
    with wave.open(str(destination), "rb") as wf:
        if wf.getnframes() == 0:
            raise RuntimeError("Gemini TTS audio is empty.")

async def speech(text: str, destination: Path) -> None:
    if not os.environ.get("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY repository secret is not set.")
    for attempt in range(3):
        try:
            await asyncio.to_thread(_generate, text, destination)
            return
        except Exception:
            if attempt == 2:
                raise
            await asyncio.sleep(5 * (attempt + 1))
