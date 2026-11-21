import subprocess,os,re,json
from pathlib import Path
from faster_whisper import WhisperModel
p=Path("father_old32_audio_QA");p.mkdir(exist_ok=True)
subprocess.run(["gh","run","download","44926295100","-n","father-decision-complete-enceladus","-D",str(p)],check=True)
audio=p/"father_important_complete.wav"
model=WhisperModel("small",device="cpu",compute_type="int8",cpu_threads=4,num_workers=2)
segments,_=model.transcribe(str(audio),language="ko",word_timestamps=True,beam_size=4,vad_filter=False,condition_on_previous_text=False)
segments=list(segments)
spoken=" ".join(s.text.strip() for s in segments)
words=[{"word":w.word,"start":w.start,"end":w.end} for s in segments for w in (s.words or [])]
print("FULL_DECISION_TTS_ASR",spoken,flush=True)
norm=lambda s:re.sub(r"[^가-힣]","",s)
ok="결정하겠다" in norm(spoken) and "남은인생" in norm(spoken)
if not ok:raise RuntimeError("Required full phrase not spoken")
report={"spoken":spoken,"full_phrase_verified":ok,"last_word_end":words[-1]["end"] if words else None,"words":words}
(p/"qa.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
print("FATHER_DECISION_ENDED_CORRECTLY",round(words[-1]["end"],3),flush=True)
