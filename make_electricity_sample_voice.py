"""One-off natural Korean male voice sample for electricity long-form redesign. No publishing."""
import json, asyncio
from pathlib import Path
import edge_tts
s=json.loads(Path("electricity_sample_voice_request.json").read_text(encoding="utf-8"))
out=Path("electricity_sample_tts");out.mkdir(exist_ok=True)
async def run():
    for i,scene in enumerate(s["scenes"]):
        output=out/f"take_{i:02d}.mp3"
        for voice in ("ko-KR-HyunsuMultilingualNeural","ko-KR-BongJinNeural","ko-KR-InJoonNeural"):
            try:
                await edge_tts.Communicate(scene["say"],voice,rate="-3%",pitch="-1Hz").save(str(output))
                if output.stat().st_size < 1500: raise RuntimeError("Audio too small")
                print("scene",i,"voice",voice,"bytes",output.stat().st_size,flush=True)
                break
            except Exception as ex:
                print("voice failed",voice,str(ex)[:170],flush=True)
        if not output.exists() or output.stat().st_size < 1500: raise RuntimeError("No narration for scene "+str(i))
        await asyncio.sleep(0.5)
asyncio.run(run())
