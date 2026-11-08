"""Single production Korean voice: scene-based for synced large Korean subtitles."""
from pathlib import Path
import json, asyncio
import edge_tts
cfg=json.loads(Path("glp1_medical_short.json").read_text(encoding="utf-8"))
out=Path("glp1_narration"); out.mkdir(exist_ok=True)
async def main():
 for idx,scene in enumerate(cfg["scenes"]):
  fn=out/f"scene_{idx:02d}.mp3"
  for attempt in range(4):
   try:
    await edge_tts.Communicate(scene["say"],cfg["voice"],rate=cfg["rate"],pitch="-1Hz").save(str(fn))
    if fn.stat().st_size < 2000: raise RuntimeError("Too small")
    print(idx,fn.stat().st_size,flush=True)
    break
   except Exception as ex:
    if attempt == 3: raise
    print("retry",idx,str(ex)[:120],flush=True)
    await asyncio.sleep(3)
  await asyncio.sleep(0.3)
asyncio.run(main())
