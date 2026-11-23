from pathlib import Path
import os,base64,time,wave,re,json,difflib,subprocess
from google import genai
from faster_whisper import WhisperModel
OUT=Path("father_diary_retake");OUT.mkdir(exist_ok=True)
LINES=[
(2,"그런데 어느 날, 초등학생 딸의 일기장을 읽다가 끝내 눈물을 흘렸습니다."),
(16,"어느 날, 딸의 책상 위에 놓인 일기장이 눈에 들어왔습니다."),
(37,"성호는 딸의 일기장을 덮고 조용히 딸을 안아주었습니다."),
(38,"그제야 그는 알았습니다. 인생의 내리막길에서도, 함께하는 저녁처럼 소중한 행복은 사라지지 않는다는 것을.")
]
client=genai.Client(http_options={"api_version":"v1beta"},api_key=os.environ["GEMINI_API_KEY"])
asr=WhisperModel("small",device="cpu",compute_type="int8",cpu_threads=4)
def norm(s):return re.sub(r"[^가-힣a-z0-9]","",s.lower())
def proc(cmd):
 p=subprocess.run(cmd,capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stderr[-1200:])
result=[]
for i,text in LINES:
 for attempt in range(5):
  try:
   style="Kore, adult Korean woman with a calm moving realistic Korean short story narrator voice. Warm and compassionate, natural spoken Korean. Clear steady conversational pace like the existing audio. No added words, no music, not a dramatic sob or theatrical reading. Fully articulate each word including final syllables. Read only the provided Korean text."
   response=client.interactions.create(model="gemini-3.8-flash-tts",input=[{"type":"user_input","content":[{"type":"text","text":text,"annotations":[{"type":"speech_metadata","style":style}]}]}],response_format={"type":"audio"},generation_config={"speech_config":[{"voice":"Kore"}]})
   data=response.output_audio.data
   if not data:raise RuntimeError("empty audio")
   raw=base64.b64decode(data) if isinstance(data,str) else data
   source=OUT/f"source_{i:02d}.wav"
   if raw[:4]==b"RIFF":source.write_bytes(raw)
   else:
    with wave.open(str(source),"wb") as w:
     w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(raw)
   final=OUT/f"clip_{i:02d}.wav"
   proc(["ffmpeg","-v","error","-y","-i",str(source),"-af","loudnorm=I=-18:TP=-1.5:LRA=10,atempo=1.25,apad=pad_dur=0.12","-ar","24000","-ac","1",str(final)])
   with wave.open(str(final)) as w:duration=w.getnframes()/w.getframerate()
   segments,_=asr.transcribe(str(final),language="ko",word_timestamps=True,beam_size=4,condition_on_previous_text=False)
   words=[{"text":v.word.strip(),"start":round(v.start,3),"end":round(v.end,3)} for s in segments for v in (s.words or [])]
   heard=" ".join(w["text"] for w in words)
   score=difflib.SequenceMatcher(None,norm(text),norm(heard),autojunk=False).ratio()
   if score<0.70 or len(norm(heard))<len(norm(text))*.72:raise RuntimeError(f"ASR mismatch score {score:.2f} heard {heard}")
   result.append({"i":i,"text":text,"file":final.name,"duration":duration,"words":words,"asr":heard,"score":round(score,3)})
   print("SUCCESS",i,round(duration,2),round(score,2),heard,flush=True)
   break
  except Exception as e:
   print("RETRY",i,attempt+1,str(e)[:170],flush=True)
   if attempt==4:raise
   time.sleep(10+attempt*9)
 time.sleep(2)
(OUT/"manifest.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf8")
print("DONE",len(result),flush=True)
