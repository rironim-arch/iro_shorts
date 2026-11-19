import json, urllib.request, pathlib, av
from faster_whisper import WhisperModel
url="https://static.metricool.com/planner/202611/7845640-file-17852607218192891611.mp4"
p=pathlib.Path("wolf_source.mp4")
urllib.request.urlretrieve(url,p)
with av.open(str(p)) as f:
    duration=float(f.duration)/1000000
print("DOWNLOADED DURATION",duration,flush=True)
model=WhisperModel("small",device="cpu",compute_type="int8")
segments,meta=model.transcribe(str(p),language="ko",beam_size=5,word_timestamps=True,condition_on_previous_text=False,vad_filter=False)
out={"duration":duration,"source":url,"language":meta.language,"segments":[]}
for s in segments:
    info={"start":round(s.start,3),"end":round(s.end,3),"text":s.text,"words":[{"start":round(w.start,3),"end":round(w.end,3),"word":w.word} for w in s.words or []]}
    print(info["start"],info["end"],info["text"],flush=True)
    out["segments"].append(info)
pathlib.Path("wolf_asr_74sec_av.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
