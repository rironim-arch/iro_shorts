from pathlib import Path
import json, asyncio
import edge_tts
r=json.loads(Path("detergent_dose_shorts.json").read_text(encoding="utf-8"))
out=Path("detergent_dose_audio");out.mkdir(exist_ok=True)
async def main():
 for i,s in enumerate(r["scenes"]):
  fn=out/f"narration_{i:02d}.mp3"
  for retry in range(4):
   try:
    await edge_tts.Communicate(s["say"],r["voice"],rate=r["rate"],pitch="-1Hz").save(str(fn))
    if fn.stat().st_size<2000: raise RuntimeError("TTS output too small")
    print(i,fn.stat().st_size,flush=True)
    break
   except Exception as ex:
    if retry==3: raise
    print("retry",i,str(ex)[:150],flush=True)
    await asyncio.sleep(4)
  await asyncio.sleep(0.3)
asyncio.run(main())
