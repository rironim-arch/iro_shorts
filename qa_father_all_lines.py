import subprocess,re,json
from pathlib import Path
from faster_whisper import WhisperModel
p=Path("father_all_lines_qa");p.mkdir(exist_ok=True)
subprocess.run(["gh","run","download","44925031906","-n","father-enceladus-voice-clips","-D",str(p)],check=True)
expected=[
"운동 끝나고 같이 차 마실 사람이 생겼다. 나, 그분하고 결혼할 생각이다.",
"너는 내가 걱정되는 거냐, 아니면 이 집이 걱정되는 거냐?",
"내가 혼자 밥을 먹는지, 어디 아픈 데는 없는지, 마지막으로 물어본 게 언제였냐.",
"네 엄마를 보내고도 오래 버텼다. 그런데 말이다, 혼자 늙어 간다는 게… 생각보다 외롭더라.",
"재산 문제는 내가 알아서 잘 정리하마. 하지만 남은 인생, 누구와 보낼지는 내가 결정하겠다.",
"내가 너희 아버지로 산 세월도 소중했다. 하지만 이제는, 나 자신으로도 좀 살아 보고 싶구나.",
"이 나이에… 다시 봄이 올 줄은 몰랐네."
]
def norm(x):return re.sub(r"[^가-힣a-z0-9]","",x.lower())
asr=WhisperModel("small",device="cpu",compute_type="int8",cpu_threads=4,num_workers=2)
results=[]
for i,text in enumerate(expected):
 source=p/f"fit_{i:02d}.wav"
 if not source.exists():source=p/f"father_{i:02d}.wav"
 segments,_=asr.transcribe(str(source),language="ko",beam_size=4,word_timestamps=True,condition_on_previous_text=False,vad_filter=False)
 segments=list(segments)
 recognized=" ".join(s.text.strip() for s in segments)
 tokens=norm(recognized)
 # Look at whether the specific clause-final word has been recognized.
 word_candidates=[norm(t) for t in text.split() if norm(t)]
 last=word_candidates[-1]
 last_present=last in tokens
 print("SEGMENT",i,"recognized=",recognized,"EXPECTED_LAST=",last,"last_present=",last_present,flush=True)
 results.append({"index":i,"expected":text,"transcribed":recognized,"last_word":last,"last_recognized":last_present})
(p/"line_qa.json").write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf8")
print("LINE_QA_DONE",sum(x["last_recognized"] for x in results),len(results),flush=True)
