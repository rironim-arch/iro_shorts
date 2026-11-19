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
    "사람들은 그를 성공한 가장이라 불렀습니다. 하지만 자식들에게 그는 두려운 아버지였습니다.",
    "젊은 날 그는 돈을 벌고, 상을 받고, 사람들의 존경을 받았습니다.",
    "그러나 현관문이 열리면 아이들은 숨을 죽였습니다.",
    "조금만 잘못해도 그는 매를 들었습니다. 어디서 말대꾸야!",
    "아내가 말려도 소용없었습니다. 그녀의 눈물조차 이해하려 하지 않았죠.",
    "그는 이 모든 게 가족을 위한 희생이라 믿었습니다.",
    "세월이 흘러 아이들은 집을 떠났고, 아내마저 먼저 세상을 떠났습니다.",
    "홀로 남은 방에는 트로피 하나와 낡은 가족사진만 있었습니다.",
    "노인은 사진을 품고 중얼거렸습니다.",
    "내가 그때 아내의 마음을 헤아리고, 아이들의 두려움을 이해했다면...",
    "그들의 아픔에 공감하는 남편이자 아버지였다면...",
    "우리 가족의 마지막은 달라지지 않았을까."
]
IMAGE_SCENES = [
    "현재: 성공한 노인이 시상식 상을 받을 때 가족이 멀리 떨어져 있는 교차 장면",
    "젊은 아버지가 회사에서 축하받는 모습. 트로피는 단 한 개만",
    "현관문 열고 들어오는 엄격한 아버지와 조용해진 가족",
    "손에 회초리를 든 아버지 앞에서 움츠린 아이들. 폭력 행위 직접 묘사 금지",
    "아내가 자녀 앞을 가로막고 울먹이는 장면",
    "홀로 직장 야근하는 아버지와 텅 빈 식탁",
    "성인이 된 아이들이 집을 떠난 뒤 아내 장례를 치르는 노인",
    "외로운 노인의 방, 트로피 한 개와 빛바랜 가족사진",
    "그가 사진을 가슴 가까이 끌어안는 장면",
    "과거의 아내 얼굴을 떠올리며 후회하는 노인",
    "유년의 아이들에게 귀 기울여주지 못했던 아버지의 회상",
    "늙은 아버지가 사진을 쓰다듬으며 눈물 흘리는 마무리"
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
