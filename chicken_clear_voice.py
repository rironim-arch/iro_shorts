"""Recreate the Korean chicken Short narration in short, clean Gemini TTS passages.

- Manual review only, no upload.
- Use stored GEMINI_API_KEY from GitHub Actions; never hardcode credentials.
- Keep original text content and CTA.
"""
import json
import os
import re
import time
import wave
from pathlib import Path

from google import genai
from google.genai import types

OUT=Path("output_chicken_clear")
OUT.mkdir(parents=True,exist_ok=True)
SECTIONS=[
    {
      "scene_ids":[0],
      "text":"먹다 남은 치킨, 며칠까지 먹어도 될까요? 어제 먹다 남은 치킨, 그냥 데워 먹어도 괜찮을까요?"
    },
    {
      "scene_ids":[1,2],
      "text":"미국 농무부와 CDC 식품안전 지침에 따르면, 먹다 남은 치킨은 4도 이하 냉장고에서 3일에서 4일 이내에 먹는 것이 권장됩니다. 하지만 중요한 건 냉장고에 넣기 전입니다."
    },
    {
      "scene_ids":[3,4],
      "text":"일반적인 실내에서는 2시간 이내에 냉장 보관하세요. 주변 온도가 32도를 넘는 더운 환경에서는 1시간 이내에 냉장고에 넣어야 합니다. 겨울이라도 난방된 실내라면 예외는 아닙니다."
    },
    {
      "scene_ids":[5],
      "text":"전자레인지로 데울 때는 중간에 한 번 뒤집고, 치킨 속까지 74도 이상 충분히 가열하세요."
    },
    {
      "scene_ids":[6,7,8],
      "text":"실온에 오래 방치한 치킨은 다시 데운다고 안전해지는 것이 아닙니다. 도움이 됐다면 구독과 좋아요! 생활알고리즘, 알아두면 쓸모 있는 생활상식!"
    },
]
api_key=os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY not configured")
client=genai.Client(api_key=api_key)
all_frames=[]
metadata=[]
rate=None
for idx,part in enumerate(SECTIONS):
    script=part["text"]
    prompt=(
        "Please read this Korean informational video narration verbatim in the warm, "
        "natural male Korean voice. SPEAK AT A SLIGHTLY RELAXED PACE, PRONOUNCE EVERY "
        "KOREAN SYLLABLE CLEARLY, do not merge, rush, truncate, or swallow the ending "
        "of words. Use a gentle brief natural pause at sentence punctuation. "
        "Do not add any text or introduction. Korean narration only.\n\n"
        +script
    )
    result=client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
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
    parts=result.candidates[0].content.parts if result.candidates else []
    candidates=[p.inline_data for p in parts if getattr(p,"inline_data",None)]
    if not candidates or not candidates[0].data:
        raise RuntimeError("Gemini returned no audio for section "+str(idx+1))
    raw=candidates[0].data
    mime=(candidates[0].mime_type or "").lower()
    if raw[:4]==b"RIFF" or "wav" in mime:
        from io import BytesIO
        with wave.open(BytesIO(raw),"rb") as w:
            nchan,sw,samplerate=w.getnchannels(),w.getsampwidth(),w.getframerate()
            frames=w.readframes(w.getnframes())
    elif "pcm" in mime or "audio/l16" in mime or not mime:
        samplerate=int(re.search(r"rate=(\d+)",mime).group(1)) if re.search(r"rate=(\d+)",mime) else 24000
        nchan,sw,frames=1,2,raw
    else:
        raise RuntimeError("Unexpected MIME: "+mime)
    if sw!=2 or nchan!=1:
        raise RuntimeError("Unexpected audio channels/format")
    if rate is None: rate=samplerate
    if rate!=samplerate:
        raise RuntimeError("Mismatch audio sample rates")
    with wave.open(str(OUT/f"section_{idx+1:02d}.wav"),"wb") as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(frames)
    length=len(frames)//2
    metadata.append({"section":idx+1,"scenes":part["scene_ids"],"text":script,"audio_duration":length/rate})
    all_frames.append(frames)
    print(f"section {idx+1}: {length/rate:.3f}s",flush=True)
    if idx<len(SECTIONS)-1:
        silence_seconds=.24
        all_frames.append(bytes(round(silence_seconds*rate)*2))
        time.sleep(2)
with wave.open(str(OUT/"chicken_charon_clear.wav"),"wb") as out:
    out.setnchannels(1)
    out.setsampwidth(2)
    out.setframerate(rate)
    out.writeframes(b"".join(all_frames))
metadata_obj={
  "voice":"Gemini Charon",
  "method":"5 separate short narrated sections with 0.24s pauses",
  "sample_rate":rate,
  "segments":metadata,
  "pause_seconds":0.24,
  "total_duration_seconds":sum(len(f)//2 for f in all_frames)/rate,
}
(OUT/"segments.json").write_text(json.dumps(metadata_obj,ensure_ascii=False,indent=2),encoding="utf-8")
(OUT/"script.txt").write_text("\n\n".join(s["text"] for s in SECTIONS)+"\n",encoding="utf-8")
print("COMPLETE",metadata_obj["total_duration_seconds"],flush=True)
