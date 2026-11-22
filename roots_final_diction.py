import os,re,time,json,wave,subprocess,difflib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from google import genai
from google.genai import types
from faster_whisper import WhisperModel
TURNS=[[12,"보렴. 뿌리는 보이지 않는 동안에도 자라고 있었단다."],[14,"너는 지난 2년 동안 아무것도 안 한 게 아니잖니."],[18,"사람들은 네가 얼마나 높이 올라갔는지만 보겠지."],[19,"하지만 이 아버지는 알고 있다."],[20,"네가 무너지지 않으려고 얼마나 애를 썼는지."]]
out=Path("roots_tts_final_retake");out.mkdir(exist_ok=True)
api=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
asr=WhisperModel("base",device="cpu",compute_type="int8",cpu_threads=4)
def norm(s):return re.sub(r"[^a-z0-9가-힣]","",s.lower())
def synth(i,script):
 for k in range(5):
  try:
   instruction=("한국어 감동 사연에 등장하는 70대 아버지의 음성입니다. "
      "아래 대사 한 문장만 자연스럽고 또렷하게 읽으세요. "
      "추가 대사, 설명, 요약, 교훈, 다른 말은 절대 하지 마세요. "
      "한 음절도 빼먹지 말고 마지막 글자까지 정확하게 말하고 끝내세요.\n"
      "대사:\n"+script)
   resp=api.models.generate_content(model="gemini-2.5-flash-preview-tts",contents=instruction,
    config=types.GenerateContentConfig(response_modalities=["AUDIO"],speech_config=types.SpeechConfig(
    voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Enceladus")))))
   data=next(p.inline_data for c in resp.candidates for p in c.content.parts if getattr(p,"inline_data",None) and getattr(p.inline_data,"data",None))
   raw=out/f"raw_{i:02d}_{k}.wav"
   if data.data[:4]==b"RIFF":raw.write_bytes(data.data)
   else:
    mtch=re.search(r"rate=(\d+)",data.mime_type or "")
    with wave.open(str(raw),"wb") as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(int(mtch.group(1)) if mtch else 24000);w.writeframes(data.data)
   with wave.open(str(raw),"rb") as w:secs=w.getnframes()/w.getframerate()
   pieces,_=asr.transcribe(str(raw),language="ko",beam_size=4,condition_on_previous_text=False,vad_filter=False)
   heard=" ".join(p.text.strip() for p in pieces)
   similarity=difflib.SequenceMatcher(None,norm(script),norm(heard),autojunk=False).ratio()
   print("QA",i,k,round(secs,3),round(similarity,3),heard,flush=True)
   key_ok= (i!=12 or "자라고" in norm(heard)) and (i!=20 or ("썼는지" in norm(heard) or "애를" in norm(heard)))
   if similarity<0.83 or secs>max(7.0,len(script)*.27) or not key_ok:
    if k<4:continue
    raise RuntimeError(f"BAD_LIPS {i}: {heard}")
   target=out/f"turn_{i:02d}.wav"
   q=subprocess.run(["ffmpeg","-y","-v","error","-i",str(raw),"-af","loudnorm=I=-18:TP=-2:LRA=8,apad=pad_dur=0.22","-ar","24000","-ac","1",str(target)],capture_output=True,text=True)
   if q.returncode:raise RuntimeError(q.stderr)
   return {"index":i,"script":script,"asr":heard,"ratio":round(similarity,3),"seconds":round(secs,3),"attempts":k+1}
  except Exception as e:
   print("RETRY",i,k,str(e)[:140],flush=True)
   if k==4:raise
   time.sleep(4+k*4)
res=[None]*len(TURNS)
with ThreadPoolExecutor(max_workers=2) as ex:
 futures={ex.submit(synth,*line):idx for idx,line in enumerate(TURNS)}
 for f in as_completed(futures):res[futures[f]]=f.result()
(out/"final_manifest.json").write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding="utf8")
print("ALL_FINAL_QA_OK",flush=True)
