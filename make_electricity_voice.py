"""One-off narration generation for two home electricity videos. Never publishes."""
import asyncio,json
from pathlib import Path
import edge_tts
req=json.loads(Path("household_electricity_2026_project.json").read_text(encoding="utf-8"))
async def main():
 for key in ("long","short"):
  folder=Path("electricity_audio")/key
  folder.mkdir(parents=True,exist_ok=True)
  for i,row in enumerate(req[key]):
   p=folder/f"scene_{i:02d}.mp3"
   for attempt in range(3):
    try:
     await edge_tts.Communicate(row["say"],"ko-KR-InJoonNeural",rate="-3%").save(str(p))
     print(key,i,p.stat().st_size,flush=True)
     break
    except Exception as e:
     if attempt==2:raise
     print("Retry",key,i,str(e)[:150],flush=True)
     await asyncio.sleep(7)
   await asyncio.sleep(0.3)
asyncio.run(main())
