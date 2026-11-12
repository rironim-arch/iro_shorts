"""Kimchi-stain Shorts: Gemini Charon voice-only draft. Manual review, never uploads."""
import asyncio
import json
import subprocess
import wave
from pathlib import Path
from gemini_charon_tts import speech

TEXT = """식당에서 흰옷에 김칫국물이 튀었다면? 당황해서 휴지로 박박 문지르지 마세요. 우선 음식물 건더기는 조심스럽게 걷어내고, 깨끗한 휴지로 톡톡 눌러 남은 국물을 흡수해 주세요. 세게 문지르면 얼룩이 더 번질 수 있어요. 집에 돌아왔다면 먼저 옷의 세탁 표시부터 확인하세요. 면이나 폴리에스터처럼 물세탁이 가능한 옷이라면, 얼룩의 뒷면에서 찬물을 흘려보내며 헹구세요. 그다음 핵심은 주방세제입니다! 눈에 띄지 않는 곳에 먼저 시험하고, 주방세제를 아주 소량 묻혀 손으로 부드럽게 애벌빨래하세요. 김칫국물에 섞인 기름기를 제거하는 데 도움을 줄 수 있어요. 주방세제는 깨끗하게 헹군 뒤 세탁 표시대로 일반 세탁하세요. 주방세제를 세탁기 안에 직접 넣지는 마세요. 얼룩이 남아 있다면 건조기는 잠깐! 열 때문에 제거가 더 어려워질 수 있어요. 실크나 드라이클리닝 전용 옷은 세탁소에 문의하는 게 안전합니다. 생활알고리즘! 도움이 됐다면 구독과 좋아요!"""

async def main():
    out = Path("kimchi_gemini_audio")
    out.mkdir(exist_ok=True)
    raw = out / "kimchi_charon_raw.wav"
    await speech(TEXT, raw)
    sped = out / "kimchi_charon_125.wav"
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(raw), "-af", "atempo=1.25", "-ar", "24000", "-ac", "1", str(sped)], check=True)
    with wave.open(str(sped), "rb") as w:
        dur = w.getnframes() / w.getframerate()
        if dur < 10: raise RuntimeError("Abnormally short TTS.")
    (out / "script.txt").write_text(TEXT, encoding="utf-8")
    (out / "metadata.json").write_text(json.dumps(
        {"voice":"Gemini 2.5 Flash TTS / Charon", "speed":1.25,
         "duration":round(dur,3), "status":"DRAFT_NOT_UPLOADED"}, ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"KIMCHI_CHARON_READY duration={dur:.2f}s")
if __name__ == "__main__":
    asyncio.run(main())
