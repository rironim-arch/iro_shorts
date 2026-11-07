"""Fallback Korean adult male neural TTS, chunked to ensure slide/voice synchronization."""
import asyncio, json, subprocess, time
from pathlib import Path
import edge_tts
request=json.loads(Path("microwave_short_request.json").read_text(encoding="utf-8"))
Path("microwave_audio").mkdir(exist_ok=True)
async def run():
 for i,scene in enumerate(request["chunks"]):
  dest=Path("microwave_audio")/f"scene_{i:02d}"
  for attempt in range(3):
   try:
    await edge_tts.Communicate(scene["say"],"ko-KR-InJoonNeural",rate="-5%").save(str(dest)+".mp3")
    print("OK",i,(dest.with_suffix(".mp3")).stat().st_size,flush=True)
    break
   except Exception as e:
    if attempt==2: raise
    print("retry",i,str(e),flush=True);await asyncio.sleep(8)
  await asyncio.sleep(0.8)
asyncio.run(run())
