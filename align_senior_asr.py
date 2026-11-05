"""One-off Korean ASR timestamps. No upload to YouTube, no schedules."""
import json, os, time
from pathlib import Path
from faster_whisper import WhisperModel

out=Path("aligned_output");out.mkdir(exist_ok=True)
sources=[Path("parts_first"),Path("parts_ending")]
model=WhisperModel("small",device="cpu",compute_type="int8",cpu_threads=4,num_workers=1)
report=[]
for chapter in range(1,13):
    src=(sources[0] if chapter<10 else sources[1])/f"chapter_{chapter:02d}.wav"
    if not src.exists(): raise FileNotFoundError(str(src))
    t0=time.time()
    segments,info=model.transcribe(str(src),language="ko",beam_size=3,
        best_of=3,word_timestamps=True,condition_on_previous_text=False,
        vad_filter=False,temperature=0)
    words=[];segs=[]
    for s in segments:
        segs.append({"start":round(s.start,3),"end":round(s.end,3),"text":s.text})
        for w in (s.words or []):
            words.append({"start":round(w.start,3),"end":round(w.end,3),
                          "word":w.word,"prob":round(w.probability,3)})
    response={"chapter":chapter,"duration":info.duration,"words":words,"segments":segs,
              "processing_seconds":round(time.time()-t0,1)}
    (out/f"asr_{chapter:02d}.json").write_text(
        json.dumps(response,ensure_ascii=False),encoding="utf-8")
    report.append([chapter,len(words),round(time.time()-t0,1)])
    print("CHAPTER",chapter,"words",len(words),"elapsed_s",round(time.time()-t0,1),flush=True)
(out/"report.json").write_text(json.dumps(report),encoding="utf-8")
