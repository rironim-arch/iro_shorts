"""One-off Korean male TTS for the rice safety Short; no YouTube publishing."""
import asyncio, json
from pathlib import Path
import edge_tts
r=json.loads(Path("rice_storage_short.json").read_text(encoding="utf-8"))
out=Path("rice_storage_audio");out.mkdir(exist_ok=True)
async def run():
    for i,scene in enumerate(r["scenes"]):
        p=out/f"scene_{i:02d}.mp3"
        for attempt in range(3):
            try:
                await edge_tts.Communicate(scene["say"],"ko-KR-InJoonNeural",rate="-3%",volume="+0%").save(str(p))
                print(i, p.stat().st_size, flush=True)
                break
            except Exception as e:
                if attempt==2: raise
                print("Retry",i,str(e)[:200],flush=True)
                await asyncio.sleep(8)
        await asyncio.sleep(0.6)
asyncio.run(run())
