#!/usr/bin/env python3
"""Fresh, chapter-locked Gemini Kore narration for '어느 늙은 노인의 마지막 후회'.
The transcript, scene timing, and SRT all derive from the exact same CHAPTERS list.
NEVER reuse audio or subtitle material from any earlier edition.
"""
import json, os, re, subprocess, time, wave
from pathlib import Path
from google import genai
from google.genai import types

OUT = Path("old_man_reboot_kore_output")
OUT.mkdir(exist_ok=True)

CHAPTERS = [
    "세월이 흘러 아이들은 하나둘 독립하여 집을 떠났습니다.",
    "그리고 아내마저 먼저 세상을 떠났습니다.",
    "아내가 세상을 떠난 뒤에도, 명절이 되어도 자식들은 찾아오지 않았습니다.",
    "평생 받아온 빛나는 트로피도 그의 외로움을 달래주지 못했습니다. 어느 날 낡은 가족사진을 바라보던 노인은 눈물을 흘렸습니다.",
    "내가 그때 아내의 마음을 조금만 더 헤아리고...",
    "아이들의 두려움과 아픔에 공감해 주는 남편이자 아버지였다면...",
    "우리 가족의 마지막은 달라지지 않았을까...",
    "여러분은 어떤 부모가 되고 싶으신가요? 공감하셨다면 구독과 좋아요 부탁드립니다."
]
IMAGE_SCENES = [
    "자녀가 성인이 되어 가방을 들고 하나둘 독립해 집을 떠나는 장면",
    "아내의 영정 사진 앞에 홀로 선 노인",
    "명절에 차린 식탁에 아무도 오지 않아 홀로 기다리는 노인",
    "트로피 하나와 낡은 가족사진을 바라보며 눈물 흘리는 노인",
    "아내의 마음을 헤아리지 못한 과거를 후회하는 노인",
    "두려워하는 아이들을 떠올리며 후회하는 노인",
    "가족사진을 가슴에 안고 눈물을 흘리는 노인",
    "여러분은 어떤 부모가 되고 싶으신가요? 구독과 좋아요 마무리"
]

assert len(CHAPTERS) == len(IMAGE_SCENES)

def run(args):
    subprocess.run(args, check=True)

def format_srt(ts):
    millis = round(ts * 1000)
    hh = millis // 3600000; millis %= 3600000
    mm = millis // 60000; millis %= 60000
    ss = millis // 1000; millis %= 1000
    return f"{hh:02}:{mm:02}:{ss:02},{millis:03}"

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
timeline = []
cursor = 0.0

for i, text in enumerate(CHAPTERS):
    prompt = (
        "다음 문장을 한국어 여성 내레이터 한 명이 담담하고 진중한 감정으로 발음이 또렷하게 읽습니다. "
        "실제 음성에는 오직 따옴표 안의 한국어 대본 내용만 담으세요. "
        "요약, 생략, 대사 추가, 배경음악, 효과음, 앞뒤 설명 금지. "
        "각 음절과 문장 끝을 온전히 발음하고 말미를 자르지 마세요. "
        "대사 인용도 같은 여성 목소리로 연기해 주세요. \n\n"
        f"대본: 「{text}」"
    )
    payload = None
    for attempt in range(5):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")
                        )
                    )
                )
            )
            for part in response.candidates[0].content.parts:
                data = getattr(part, "inline_data", None)
                if data and data.data:
                    payload = data
                    break
            if payload:
                break
        except Exception as exc:
            print(f"RETRY scene={i+1}, attempt={attempt+1}, reason={str(exc)[:200]}", flush=True)
        time.sleep(5 * (attempt + 1))
    if payload is None:
        raise RuntimeError(f"SCENE_{i+1}_NO_AUDIO_NO_FAKE_OUTPUT")
    wav = OUT / f"raw_{i:02}.wav"
    if payload.data[:4] == b"RIFF":
        wav.write_bytes(payload.data)
    else:
        match = re.search(r"rate=(\d+)", payload.mime_type or "")
        rate = int(match.group(1)) if match else 24000
        with wave.open(str(wav), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(rate)
            wf.writeframes(payload.data)
    chapter_file = OUT / f"scene_{i:02}_kore_125.wav"
    # Fixed 1.25x rate; avoid chopping first/last syllables with padded silence.
    run(["ffmpeg", "-y", "-v", "error", "-i", str(wav),
         "-af", "atempo=1.25,loudnorm=I=-17:TP=-2:LRA=11,adelay=150,apad=pad_dur=0.20",
         "-ar", "24000", "-ac", "1", str(chapter_file)])
    with wave.open(str(chapter_file), "rb") as wf:
        duration = wf.getnframes() / wf.getframerate()
    if duration < 0.5:
        raise RuntimeError(f"SCENE_{i+1}_TOO_SHORT")
    timeline.append({
        "scene": i+1, "start": round(cursor, 3),
        "end": round(cursor + duration, 3), "duration": round(duration, 3),
        "text": text, "image_scene": IMAGE_SCENES[i]
    })
    cursor += duration
    print(f"SCENE_{i+1} {duration:.3f}s total {cursor:.3f}s", flush=True)
    time.sleep(0.6)

concat = OUT / "concat.txt"
concat.write_text("\n".join(f"file 'scene_{i:02}_kore_125.wav'" for i in range(len(CHAPTERS))) + "\n", encoding="utf-8")
master = OUT / "old_man_reboot_kore_125.wav"
run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(concat),
     "-c:a", "pcm_s16le", str(master)])
run(["ffmpeg", "-y", "-v", "error", "-i", str(master),
     "-b:a", "160k", str(OUT / "old_man_reboot_kore_125.mp3")])
srt = []
for row in timeline:
    srt.extend([
        str(row["scene"]),
        f'{format_srt(row["start"])} --> {format_srt(row["end"])}',
        row["text"], ""
    ])
(OUT / "old_man_reboot_kore_125.srt").write_text("\n".join(srt), encoding="utf-8")
(OUT / "timing.json").write_text(json.dumps({
    "title": "어느 늙은 노인의 마지막 후회",
    "tts_engine": "gemini-2.5-flash-preview-tts",
    "voice": "Kore", "speed": 1.25,
    "total_seconds": round(cursor,3), "scenes": timeline
}, ensure_ascii=False, indent=2), encoding="utf-8")
print("VOICE_COMPLETE exact_duration", round(cursor,3), "seconds", flush=True)
