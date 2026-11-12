"""Kimchi stain: Gemini 2.5 Flash TTS Charon, user-approved voice, no upload."""
import asyncio
import json
import wave
from pathlib import Path
from gemini_charon_tts import speech

TEXT = """식당에서 흰옷에 김칫국물이 튀었다면? 휴지로 박박 문지르지 마세요. 먼저 건더기를 걷어내고 깨끗한 휴지로 톡톡 눌러주세요. 집에서는 세탁 표시부터 확인하세요. 물세탁 가능한 옷이라면 얼룩 뒷면에서 찬물로 헹구세요. 여기서 중요한 건 주방세제! 얼룩에 주방세제를 소량 바르고 부드럽게 애벌빨래하세요. 기름기 제거에 도움이 됩니다. 다만 눈에 띄지 않는 곳에 먼저 시험하세요. 충분히 헹군 다음 세탁 표시대로 세탁기에 넣으세요. 주방세제를 직접 세탁기에 넣으면 안 됩니다. 얼룩이 남으면 건조기는 피하세요. 열 때문에 제거가 더 어려워질 수 있습니다. 실크나 드라이클리닝 전용 옷에는 사용하지 마세요. 생활알고리즘! 도움이 됐다면 구독과 좋아요!"""

async def main():
    out = Path("kimchi_gemini_audio")
    out.mkdir(exist_ok=True)
    raw = out / "kimchi_charon_raw.wav"
    await speech(TEXT, raw)
    with wave.open(str(raw), "rb") as w:
        duration = w.getnframes() / w.getframerate()
        if duration < 20: raise RuntimeError("Abnormally short Gemini audio.")
    (out / "script.txt").write_text(TEXT, encoding="utf-8")
    (out / "metadata.json").write_text(json.dumps({
        "voice":"Gemini 2.5 Flash TTS / Charon", "target_speed":1.25,
        "raw_duration":round(duration,3), "status":"DRAFT_NOT_UPLOADED"
    },ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"KIMCHI_CHARON_RAW_READY duration={duration:.2f}s")
if __name__ == "__main__":
    asyncio.run(main())
