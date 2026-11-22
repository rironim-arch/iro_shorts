import os,re,time,json,wave,subprocess,difflib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from google import genai
from google.genai import types
from faster_whisper import WhisperModel
TURNS=[[7,"저 나무, 처음 심었을 때 기억나냐?"],[9,"겉으로는 안 자란 것 같지?"],[12,"보렴. 보이지 않는 동안에도 뿌리는 자라고 있었단다."],[14,"너도 지난 2년 동안 아무것도 안 한 게 아니잖니."],[15,"떨어져도 다시 면접을 봤고, 새로운 공부도 시작했지."],[16,"힘든 와중에도 아픈 엄마 병원에 꼬박꼬박 모시고 갔고."],[18,"남들은 네가 얼마나 높이 올라갔는지만 보겠지."],[19,"하지만 아버지는 안다."],[20,"네가 무너지지 않으려고 얼마나 애썼는지."]]
out=Path("roots_tts_retake");out.mkdir(exist_ok=True)
api=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
model=WhisperModel("base",device="cpu",compute_type="int8",cpu_threads=4)
def clean(s):return re.sub(r"[^a-z0-9가-힣]","",s.lower())
def f(i,line):
 for k in range(6):
  try:
   # Never include any other dialogue line or example in the prompt.
   prompt=("당신은 70대 한국인 아버지 역의 남성 성우입니다. "
      "아래에 적힌 한 문장만 따뜻하고 분명한 한국어로 끝까지 읽어 주세요. "
      "문장 뒤에는 아무 말도 덧붙이지 마세요. 역할 설명, 해설, 요약, 교훈도 말하지 마세요. "
      "특히 마지막 음절까지 발음한 다음 끝내세요.\n\n읽을 문장:\n"+line)
   r=api.models.generate_content(model="gemini-2.5-flash-preview-tts",contents=prompt,
     config=types.GenerateContentConfig(response_modalities=["AUDIO"],speech_config=types.SpeechConfig(
     voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Enceladus")))))
   x=next(p.inline_data for cand in r.candidates for p in cand.content.parts if getattr(p,"inline_data",None) and getattr(p.inline_data,"data",None))
   raw=out/f"raw_{i:02d}_{k}.wav";dest=out/f"turn_{i:02d}.wav"
   if x.data[:4]==b"RIFF":raw.write_bytes(x.data)
   else:
    rate=int((re.search(r"rate=(\d+)",x.mime_type or "") or [None,"24000"])[1])
    with wave.open(str(raw),"wb") as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(x.data)
   with wave.open(str(raw),"rb") as w:secs=w.getnframes()/w.getframerate()
   chunks,_=model.transcribe(str(raw),language="ko",beam_size=3,condition_on_previous_text=False,vad_filter=False)
   heard=" ".join(ch.text.strip() for ch in chunks)
   score=difflib.SequenceMatcher(None,clean(line),clean(heard),autojunk=False).ratio()
   print(f"FATHER_QA {i:02d} take{k+1} sec{secs:.2f} score{score:.3f} ASR[{heard}]",flush=True)
   if score < .79 or secs>max(7.5,len(line)*.32):
    if k<5:time.sleep(1);continue
    raise RuntimeError(f"FAILED ASR {i} {heard}")
   q=subprocess.run(["ffmpeg","-y","-v","error","-i",str(raw),"-af","loudnorm=I=-18:TP=-2:LRA=8,apad=pad_dur=0.22","-ar","24000","-ac","1",str(dest)],capture_output=True,text=True)
   if q.returncode:raise RuntimeError(q.stderr)
   return {"index":i,"script":line,"asr":heard,"ratio":round(score,3),"seconds":round(secs,3),"takes":k+1}
  except Exception as e:
   print("ERROR",i,k,str(e)[:200],flush=True)
   if k==5:raise
   time.sleep(3+k*3)
result=[None]*len(TURNS)
with ThreadPoolExecutor(max_workers=2) as ex:
 fs={ex.submit(f,*row):j for j,row in enumerate(TURNS)}
 for ft in as_completed(fs):result[fs[ft]]=ft.result()
assert len(list(out.glob("turn_*.wav")))==len(TURNS)
(out/"retake_manifest.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
print("RETAKE_OK",len(result),flush=True)
