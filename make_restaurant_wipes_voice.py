from pathlib import Path
import json, asyncio
import edge_tts
r=json.loads(Path("restaurant_wipes_short.json").read_text(encoding="utf-8"))
out=Path("restaurant_wipes_voice");out.mkdir(exist_ok=True)
async def main():
 for i,s in enumerate(r["scenes"]):
  p=out/f"scene_{i:02d}.mp3"
  for j in range(4):
   try:
    await edge_tts.Communicate(s["say"],r["voice"],rate=r["rate"],pitch="-1Hz").save(str(p))
    if p.stat().st_size<1900: raise RuntimeError("Audio too small")
    print("ok",i,p.stat().st_size,flush=True)
    break
   except Exception as ex:
    if j==3:raise
    print("retry",i,str(ex)[:120],flush=True)
    await asyncio.sleep(4)
  await asyncio.sleep(.25)
asyncio.run(main())
