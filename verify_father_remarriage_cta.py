from pathlib import Path
import os,re,json,subprocess
from faster_whisper import WhisperModel
p=Path("father_remarriage_cta_verify");p.mkdir(exist_ok=True)
subprocess.run(["gh","run","download","44922727161","-n","father-remarriage-kore-cta","-D",str(p)],check=True)
f=p/"cta_kore.wav"
model=WhisperModel("small",device="cpu",compute_type="int8",cpu_threads=4,num_workers=2)
segs,_=model.transcribe(str(f),language="ko",beam_size=4,vad_filter=False)
txt=" ".join(s.text for s in segs)
print("CTA_WHISPER_TRANSCRIPT",txt,flush=True)
observed=re.sub(r"[^가-힣]","",txt)
ok=all(x in observed for x in ["구독","좋아요","부탁"])
(p/"verification.json").write_text(json.dumps({"transcript":txt,"CTA_complete":ok},ensure_ascii=False),encoding="utf8")
if not ok:raise RuntimeError("Final CTA not recognized as full")
print("CTA_COMPLETE_VERIFIED",flush=True)
