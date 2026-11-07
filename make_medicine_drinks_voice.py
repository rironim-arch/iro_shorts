"""Narrate medicine and drinks short with synced Korean male voice. No YouTube upload."""
import asyncio,json
from pathlib import Path
import edge_tts
r=json.loads(Path("medicine_drinks_short.json").read_text(encoding="utf-8"))
Path("medicine_drinks_audio").mkdir(exist_ok=True)
async def run():
 for i,scene in enumerate(r["scenes"]):
  p=Path("medicine_drinks_audio")/f"scene_{i:02d}.mp3"
  for attempt in range(3):
   try:
    await edge_tts.Communicate(scene["speak"],"ko-KR-InJoonNeural",rate="-5%").save(str(p))
    print(i,p.stat().st_size,flush=True)
    break
   except Exception as e:
    if attempt==2: raise
    print("retry",i,str(e),flush=True)
    await asyncio.sleep(8)
  await asyncio.sleep(0.6)
asyncio.run(run())
