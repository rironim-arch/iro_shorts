from pathlib import Path
import os,json
from openai import OpenAI
p=Path("source_voice")
wav=next(p.rglob("full.wav"))
client=OpenAI(api_key=os.environ["OPENAI_API_KEY"],timeout=100,max_retries=1)
with wav.open("rb") as stream:
    r=client.audio.transcriptions.create(model="whisper-1",file=stream,language="ko",response_format="verbose_json",timestamp_granularities=["word"],prompt="까미, 시골 장터, 검은 강아지, 대문 앞, 꿈속, 언젠가 천국에서 꼭 다시 만나자")
words=[{"text":w.word,"start":round(w.start,3),"end":round(w.end,3)} for w in r.words]
Path("kkami_kore_v2_word_times.json").write_text(json.dumps({"text":r.text,"words":words},ensure_ascii=False,indent=2),encoding="utf8")
print("KORE_ASR_DONE",len(words),"words",flush=True)
