from pathlib import Path
import wave,subprocess,json,os
from openai import OpenAI
root=Path("batches")
files=[]
for i in range(1,11):
 f=next(root.rglob(f"clip_{i:02d}.wav"),None)
 if f is None:raise RuntimeError(f"Missing audio {i}")
 files.append(f)
with Path("kore_concat.txt").open("w") as o:
 for f in files:o.write("file '"+str(f.resolve())+"'\n")
p=subprocess.run(["ffmpeg","-v","error","-y","-f","concat","-safe","0","-i","kore_concat.txt","-ar","24000","-ac","1","kore_full.wav"],capture_output=True,text=True)
if p.returncode:raise RuntimeError(p.stderr)
client=OpenAI(api_key=os.environ["OPENAI_API_KEY"],timeout=110,max_retries=1)
with open("kore_full.wav","rb") as f:
 r=client.audio.transcriptions.create(model="whisper-1",file=f,language="ko",response_format="verbose_json",timestamp_granularities=["word"],prompt="까미, 검은 강아지, 꿈속에서 마지막 배웅, 우리 천국에서 다시 만나자")
out={"text":r.text,"words":[{"text":w.word,"start":w.start,"end":w.end} for w in r.words]}
Path("kkami_kore_v2_word_times.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf8")
print("BATCH_ASR_SUCCESS",len(out["words"]),"words",flush=True)
