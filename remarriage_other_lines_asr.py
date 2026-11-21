import subprocess,re,json
from pathlib import Path
from faster_whisper import WhisperModel
out=Path("father_other_lines_qa");out.mkdir(exist_ok=True)
subprocess.run(["gh","run","download","44922224985","-n","father-remarriage-gemini-3voices","-D",str(out)],check=True)
other=[
("narrator_00.wav","각서였습니다"),("narrator_01.wav","보냈죠"),
("narrator_02.wav","다녔습니다"),("narrator_03.wav","꺼냈죠"),
("narrator_04.wav","굳어졌습니다"),("narrator_05.wav","있었죠"),
("narrator_08.wav","꺼냈습니다"),
("son_00.wav","돼요"),("son_02.wav","어떡해요"),("son_03.wav","주세요")
]
asr=WhisperModel("small",device="cpu",compute_type="int8",cpu_threads=4,num_workers=2)
norm=lambda s:re.sub(r"[^가-힣]","",s)
results=[]
for name,target in other:
 src=out/name
 s,_=asr.transcribe(str(src),language="ko",beam_size=4,word_timestamps=True,condition_on_previous_text=False,vad_filter=False)
 text=" ".join(t.text.strip() for t in s)
 ok=norm(target) in norm(text)
 results.append({"name":name,"expected_last":target,"asr":text,"end_recognized":ok})
 print("QA",name,text,"LAST_WORD",target,"PRESENT",ok,flush=True)
(out/"all_other_qa.json").write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf8")
print("NON_ELDER_ALL_LINES_QA_COMPLETED",sum(x["end_recognized"] for x in results),len(results),flush=True)
