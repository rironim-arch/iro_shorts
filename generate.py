"""생활알고리즘: one test Short, no publishing. Runs in GitHub Actions."""
import os
import math
import wave
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from google import genai
from google.genai import types

OUT = Path("output")
OUT.mkdir(exist_ok=True)
W, H = 1080, 1920
TOPIC = "샴푸, 많이 쓰면 더 깨끗할까?"
SENTENCES = [
    "샴푸, 많이 쓰면 더 깨끗할까요?",
    "꼭 그렇지는 않습니다.",
    "거품의 양이 세정력과 정확히 비례하는 건 아닙니다.",
    "두피와 모발 길이에 맞춰 적당량을 쓰세요.",
    "중요한 건 충분히 헹구는 습관입니다.",
    "매일 써먹는 생활정보, 생활알고리즘!",
]
SCRIPT = " ".join(SENTENCES)
(OUT / "script.txt").write_text(TOPIC + "\n\n" + SCRIPT + "\n", encoding="utf-8")


def create_voice():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is missing")
    client = genai.Client(api_key=key)
    model = os.getenv("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")
    prompt = (
        "Read the following Korean short-form video narration in a warm, clear, "
        "energetic Korean male speaking voice. Pronounce Korean naturally, "
        "without adding words. Moderate conversational speed.\n\n" + SCRIPT
    )
    response = client.models.generate_content(
        model=model,
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
        raise RuntimeError("Gemini returned no audio candidates.")
    parts = response.candidates[0].content.parts
    audio_parts = [p.inline_data for p in parts if getattr(p, "inline_data", None)]
    if not audio_parts:
        raise RuntimeError("Gemini returned no audio payload.")
    audio = audio_parts[0]
    raw = audio.data
    mime = (audio.mime_type or "").lower()
    if not raw:
        raise RuntimeError("Gemini audio is empty.")
    # Gemini TTS default output is 24 kHz, 16-bit mono PCM.
    if "wav" in mime or raw[:4] == b"RIFF":
        (OUT / "voice.wav").write_bytes(raw)
    elif "pcm" in mime or "audio/l16" in mime or not mime:
        rate = 24000
        import re
        found = re.search(r"rate=(\d+)", mime)
        if found:
            rate = int(found.group(1))
        with wave.open(str(OUT / "voice.wav"), "wb") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(rate)
            f.writeframes(raw)
    else:
        raise RuntimeError("Unexpected TTS audio format: " + mime)
    p = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(OUT / "voice.wav")],
        text=True, capture_output=True, check=True,
    )
    return float(p.stdout.strip())


def font(size):
    paths = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "C:/Windows/Fonts/malgunbd.ttf",
    ]
    for path in paths:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size, index=0)
    raise FileNotFoundError("Korean font missing")


def wrap(draw, value, f, limit=880):
    words = value.split()
    lines, line = [], ""
    for word in words:
        test = (line + " " + word).strip()
        if draw.textbbox((0, 0), test, font=f)[2] > limit and line:
            lines.append(line)
            line = word
        else:
            line = test
    if line:
        lines.append(line)
    return lines


def make_frame(index, sentence):
    image = Image.new("RGB", (W, H), (10, 25, 42))
    d = ImageDraw.Draw(image)
    d.rounded_rectangle((54, 60, W-54, 205), radius=42, fill=(14, 81, 104))
    d.text((W//2, 128), "생활알고리즘", font=font(81), fill="#FFFFFF", anchor="mm")
    d.text((W//2, 266), "오늘의 생활 상식", font=font(43), fill="#70D8D1", anchor="mm")
    d.ellipse((235, 360, 845, 970), fill=(23, 65, 94))
    d.ellipse((325, 455, 755, 885), outline=(65, 207, 198), width=20)
    d.text((W//2, 663), "알고 계셨나요?", font=font(66), fill="#E9FFFF", anchor="mm")
    d.rounded_rectangle((58, 1050, 1022, 1530), radius=50, fill=(244, 248, 252))
    f = font(76 if len(sentence) < 26 else 66)
    lines = wrap(d, sentence, f)
    line_height = 103
    y = 1290 - ((len(lines)-1) * line_height // 2)
    for line in lines:
        d.text((W//2, y), line, font=f, fill=(8, 35, 55), anchor="mm",
               stroke_width=0)
        y += line_height
    d.text((W//2, 1650), "구독 · 좋아요", font=font(58), fill="#F8E686", anchor="mm")
    d.text((W//2, 1745), "매일 쓸모 있는 정보", font=font(40), fill="#FFFFFF", anchor="mm")
    image.save(OUT / f"slide_{index:02d}.png")


def srt_clock(value):
    ms = round(value * 1000)
    hh, rem = divmod(ms, 3600000)
    mm, rem = divmod(rem, 60000)
    ss, rem = divmod(rem, 1000)
    return f"{hh:02}:{mm:02}:{ss:02},{rem:03}"


def main():
    duration = create_voice()
    weights = [max(1, len(s.replace(" ", ""))) for s in SENTENCES]
    weights_total = sum(weights)
    # Speech is generated as one clip; caption windows are estimates, not forced alignment.
    boundaries = [0.0]
    for n in weights:
        boundaries.append(boundaries[-1] + duration * n / weights_total)
    boundaries[-1] = duration
    captions = []
    concat = []
    for i, sentence in enumerate(SENTENCES):
        make_frame(i, sentence)
        start, end = boundaries[i], boundaries[i+1]
        captions.append(f"{i+1}\n{srt_clock(start)} --> {srt_clock(end)}\n{sentence}\n")
        concat.extend([f"file 'slide_{i:02d}.png'", f"duration {end-start:.4f}"])
    concat.append(f"file 'slide_{len(SENTENCES)-1:02d}.png'")
    (OUT / "captions.srt").write_text("\n".join(captions), encoding="utf-8")
    (OUT / "slides.txt").write_text("\n".join(concat) + "\n", encoding="utf-8")
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-safe", "0", "-f", "concat", "-i", "slides.txt",
         "-i", "voice.wav", "-map", "0:v:0", "-map", "1:a:0",
         "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "23", "-c:a", "aac", "-b:a", "128k",
         "-t", str(duration), "-movflags", "+faststart", "short.mp4"],
        cwd=OUT, check=True,
    )
    print(f"Produced {OUT / 'short.mp4'} duration={duration:.1f}s")


if __name__ == "__main__":
    main()
