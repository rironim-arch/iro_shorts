"""Generate only voice WAVs + timing manifest; avoids FFmpeg/apt GitHub runner stalls."""
import ast
import asyncio
import json
import wave
from pathlib import Path
from gemini_charon_tts import speech

CODE=Path("make_coffee_three_uses_new.py").read_text(encoding="utf-8")
tree=ast.parse(CODE)
node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="SCENES" for t in n.targets))
scenes=ast.literal_eval(node.value)
assert len(scenes)==11
assert all("구독" not in line and "좋아요" not in line and "구독" not in caption and "좋아요" not in caption for line,caption,_ in scenes[:-1])
assert scenes[-1][0].count("구독과 좋아요")==1
out=Path("coffee_three_uses_voice");out.mkdir(exist_ok=True)
async def main():
 manifest=[];cursor=0
 for i,(line,caption,visual) in enumerate(scenes):
  path=out/f"narration_{i:02}.wav"
  await speech(line,path)
  with wave.open(str(path),"rb") as w:
   secs=w.getnframes()/w.getframerate()/1.25
  manifest.append({"index":i,"line":line,"caption":caption,"visual":visual,"file":path.name,"duration_at_1_25":secs,"start_at_1_25":cursor})
  cursor+=secs
  print("VOICE",i+1,"duration",round(secs,2),flush=True)
 (out/"manifest.json").write_text(json.dumps({"scenes":manifest,"duration_seconds":cursor,"voice":"Charon","speed":1.25,"cta_only_last":True},ensure_ascii=False,indent=2))
 print("VOICE_COMPLETE",round(cursor,2))
if __name__=="__main__":asyncio.run(main())
