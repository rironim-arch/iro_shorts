from pathlib import Path
import os,json
from openai import OpenAI
P=Path("input_audio")
wav=next(P.rglob("full.wav"))
client=OpenAI(api_key=os.environ["OPENAI_API_KEY"],timeout=90,max_retries=1)
print("ASR_START",wav.stat().st_size,flush=True)
with wav.open("rb") as f:
 result=client.audio.transcriptions.create(
  model="whisper-1",file=f,response_format="verbose_json",
  timestamp_granularities=["word"],language="ko",
  prompt="까미, 검은 강아지, 시골 장터, 마지막 꿈, 우리 천국에서 다시 만나자"
 )
out={"transcript":result.text,"words":[{"text":w.word,"start":w.start,"end":w.end} for w in result.words]}
Path("kkami_asr.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf8")
print("ASR_DONE",len(out["words"]),"words",len(result.text),"chars",flush=True)
