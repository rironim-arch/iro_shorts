#!/usr/bin/env python3
"""Word timestamps/QA on a SINGLE Gemini Kore recording. Does not create new voices."""
import os,re,subprocess,json,difflib,unicodedata,wave
from pathlib import Path
from faster_whisper import WhisperModel
OUT=Path("super_owner_asr_output");OUT.mkdir(exist_ok=True)
run=os.getenv("SOURCE_VOICE_RUN_ID")
if not run:raise RuntimeError("Run id missing")
subprocess.run(["gh","run","download",run,"-n","super-owner-kore-single-voice","-D",str(OUT/"voice")],check=True)
audio=OUT/"voice"/"gemini_kore_one_take.wav"
data=json.loads((OUT/"voice"/"script.json").read_text(encoding="utf8"))
LINES=data["script"]
assert audio.exists() and len(LINES)>15
with wave.open(str(audio)) as f:duration=f.getnframes()/f.getframerate()
print("ASR_MODEL_LOADING",duration,flush=True)
model=WhisperModel("small",device="cpu",compute_type="int8",cpu_threads=4,num_workers=2)
segments,info=model.transcribe(str(audio),language="ko",word_timestamps=True,beam_size=4,
    vad_filter=False,condition_on_previous_text=False,initial_prompt="2000년대 우리 동네 슈퍼 계주 계돈 5억 원 야반도주")
segments=list(segments)
words=[]
for seg in segments:
 if seg.words:
  words.extend([{"word":w.word,"start":round(float(w.start),3),"end":round(float(w.end),3)} for w in seg.words if w.word.strip()])
asr=" ".join(s.text.strip() for s in segments)
(OUT/"asr_transcript.txt").write_text(asr+"\n",encoding="utf8")
(OUT/"words.json").write_text(json.dumps(words,ensure_ascii=False,indent=2),encoding="utf8")
def norm(s):return re.sub(r"[^가-힣A-Za-z0-9]",'',unicodedata.normalize("NFKC",s)).lower()
expected=norm("".join(LINES));observed=norm(asr)
ratio=difflib.SequenceMatcher(None,expected,observed,autojunk=False).ratio()
last=norm(" ".join(w["word"] for w in words[-30:]))
if len(words)<45:raise RuntimeError("ASR too few words")
if not all(x in last for x in ["구독","좋아요","부탁"]):
 raise RuntimeError("Last phrase absent from recognized TTS: "+last[-180:])
if ratio<0.48:raise RuntimeError(f"ASR script transcript ratio only {ratio:.3f}")
report={"voice":"Gemini Kore","single_take":True,"audio_seconds":round(duration,3),
    "asr_similarity":round(ratio,3),"recognized_words":len(words),
    "last_phrase":True,"transcript":asr,"review_status":"NEEDS_FINAL_LISTENING_CHECK"}
(OUT/"audio_qa.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
print("ASR_VERIFIED",json.dumps({k:v for k,v in report.items() if k!="transcript"},ensure_ascii=False),flush=True)
