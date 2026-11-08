"""Create 10 syncable Korean male narration clips for 생활알고리즘 dog shampoo short."""
import asyncio, json
from pathlib import Path
import edge_tts
r=json.loads(Path("dog_shampoo_short.json").read_text(encoding="utf-8"))
folder=Path("dog_shampoo_voice");folder.mkdir(exist_ok=True)
async def generate():
  for i,s in enumerate(r["scenes"]):
    path=folder/f"scene_{i:02d}.mp3"
    for attempt in range(3):
      try:
        await edge_tts.Communicate(s["say"],"ko-KR-HyunsuMultilingualNeural",rate="+20%").save(str(path))
        print(f"scene={i} bytes={path.stat().st_size}",flush=True)
        break
      except Exception as e:
        if attempt==2: raise
        print("retry",i,str(e)[:200],flush=True)
        await asyncio.sleep(5)
    await asyncio.sleep(0.5)
asyncio.run(generate())
