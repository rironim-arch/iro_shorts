from pathlib import Path
import os,time,base64,wave,re,json,difflib,subprocess
from google import genai
from faster_whisper import WhisperModel
TURN_LIST=[["n","hook","15년을 일한 김 과장의 월급은 350만 원. 그런데 얼마 전 입사한 신입사원과 똑같았습니다."],["n","career","김 과장은 생산관리부터 설비 문제, 거래처 대응까지 도맡아 왔습니다."],["n","career","하지만 그의 월급은 3년째 동결이었습니다."],["k","confront","사장님, 제가 여기서 15년을 일했습니다."],["k","confront","그런데 이번에 들어온 신입사원이 저랑 월급이 똑같더군요."],["n","confront","사장은 순간 표정이 굳었습니다."],["b","boss","이래서 내가 직원들끼리 월급 공개하지 말라고 했건만."],["b","boss","그걸 왜 서로 얘기해? 요즘 젊은 사람 뽑으려면 그 정도는 줘야 해."],["k","confront","그럼 15년 동안 일한 제 경력은 뭡니까?"],["b","boss","회사 사정 뻔히 알면서 왜 그래? 그렇게 불만이면 다른 회사 알아보든가."],["n","resign","김 과장은 더 이상 대꾸하지 않았습니다."],["n","resign","두 달 뒤, 김 과장은 업무를 인계하고 조용히 사직서를 냈습니다."],["b","resign","저 나이에 다른 회사 들어가기도 쉽지 않을 텐데. 참 안타깝네."],["n","resign","하지만 사장은 그를 붙잡지 않았습니다. 사람이야 다시 뽑으면 된다고 생각했죠."],["n","crisis","그러나 김 과장이 떠난 뒤 회사에선 문제가 하나둘 터졌습니다."],["n","crisis","오래된 설비가 멈춰도 원인을 아는 사람이 없었습니다."],["n","crisis","품질 문제에 대한 대응도 늦어졌고, 거래처는 결국 발주량을 줄였습니다."],["n","crisis","신입 직원들도 열심히 일했지만, 15년의 경험을 단번에 대신할 수는 없었습니다."],["n","phone","그렇게 6개월 뒤, 사장은 결국 김 과장에게 전화를 걸었습니다."],["b","phone","김 과장, 다시 돌아오게. 월급 450만 원 주겠네."],["k","newjob","죄송합니다. 지금 다른 회사에서 잘 다니고 있습니다."],["b","phone","거긴 얼마나 주는데?"],["k","newjob","400만 원입니다."],["b","phone","내가 450만 원 준다는데 왜 안 온다는 거야?"],["k","newjob","여기서는 제가 15년 동안 쌓은 경력을 인정해 줍니다."],["k","newjob","사장님은 제가 떠나고 나서야 그 가치를 아셨잖아요."],["n","ending","전화를 끊은 사장은 한동안 아무 말도 하지 못했습니다."],["n","ending","그는 김 과장이 나이 때문에 갈 데가 없을 거라 생각했습니다. 하지만 정작 어려움에 빠진 건 자신이었습니다."],["n","ending","월급 몇십만 원을 아끼려다, 15년의 경험과 신뢰를 잃어버린 것입니다."],["n","endcard","이 이야기가 마음에 남으셨다면 구독과 좋아요 부탁드립니다."]]
OUT=Path("salary15_gemini");OUT.mkdir(exist_ok=True)
client=genai.Client(http_options={"api_version":"v1beta"},api_key=os.environ["GEMINI_API_KEY"])
asr=WhisperModel("small",device="cpu",compute_type="int8",cpu_threads=4)
STYLE={
"n":"Voice Kore. A warm Korean adult woman narrating a believable short Korean drama, nuanced human sentiment, quiet clear articulation; conversational steady pace, not exaggerated and not robotic. Absolutely no English, no other words, no music.",
"k":"Voice Orus. A Korean factory production manager in his early 50s, competent and dignified. Speaks naturally with controlled frustration in the salary confrontation, firm yet respectful during the later phone call. Not theatrical and no yelling.",
"b":"Voice Algenib. Older Korean male company owner in his late 60s. Starts defensive, arrogant and a little condescending, later worried and regretful; natural subtle Korean conversational acting, not theatrical and do not shout."
}
VOICES={"n":"Kore","k":"Orus","b":"Algenib"}
def norm(s):
 s=s.lower().replace("15","십오").replace("350","삼백오십").replace("400","사백").replace("450","사백오십").replace("3","삼").replace("6","육")
 return re.sub("[^가-힣a-z0-9]","",s)
def proc(args):
 r=subprocess.run(args,text=True,capture_output=True)
 if r.returncode:raise RuntimeError(r.stderr[-1200:])
def stamp(s):
 x=round(s*1000);h,x=divmod(x,3600000);m,x=divmod(x,60000);s,ms=divmod(x,1000)
 return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
result=[]
t=0.0
for i,(role,scene,script) in enumerate(TURN_LIST,1):
 error=None
 for attempt in range(5):
  try:
   response=client.interactions.create(model="gemini-3.8-flash-tts",input=[{"type":"user_input","content":[{"type":"text","text":script,"annotations":[{"type":"speech_metadata","style":STYLE[role]+" Read the exact entire Korean sentence, no additions or headings. End all final syllables fully and cleanly."}]}]}],response_format={"type":"audio"},generation_config={"speech_config":[{"voice":VOICES[role]}]})
   a=response.output_audio.data
   if not a:raise RuntimeError("No data")
   data=base64.b64decode(a) if isinstance(a,str) else a
   src=OUT/f"raw_{i:02d}.wav"
   if data[:4]==b"RIFF":src.write_bytes(data)
   else:
    with wave.open(str(src),"wb") as w:
     w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(data)
   sped=OUT/f"clip_{i:02d}.wav"
   proc(["ffmpeg","-y","-v","error","-i",str(src),"-af","loudnorm=I=-18:TP=-1.5:LRA=10,atempo=1.25,apad=pad_dur=0.10","-ar","24000","-ac","1",str(sped)])
   with wave.open(str(sped)) as w:duration=w.getnframes()/w.getframerate()
   if not (.65<duration<30):raise RuntimeError(f"bad duration {duration}")
   segs,inf=asr.transcribe(str(sped),language="ko",word_timestamps=True,beam_size=4,condition_on_previous_text=False,vad_filter=False)
   words=[];heard=[]
   for seg in segs:
    for v in seg.words or []:
     words.append({"text":v.word.strip(),"start":max(0,round(v.start,3)),"end":min(duration,round(v.end,3)),"probability":round(v.probability,3)})
     heard.append(v.word.strip())
   spoken=" ".join(heard)
   match=difflib.SequenceMatcher(None,norm(script),norm(spoken),autojunk=False).ratio()
   if match<(.63 if len(norm(script))>14 else .53) or len(norm(spoken))<.55*len(norm(script)):
    raise RuntimeError(f"ASR mismatch score={match:.2f}: {spoken}")
   record={"i":i,"role":role,"scene":scene,"text":script,"voice":VOICES[role],"file":sped.name,"start":round(t,4),"end":round(t+duration,4),"duration":round(duration,4),"words":words,"asr":spoken,"asr_match":round(match,3)}
   print("PASSED",i,scene,VOICES[role],round(duration,2),round(match,2),flush=True)
   result.append(record);t+=duration
   break
  except Exception as e:
   error=str(e)
   print("RETRY",i,attempt+1,error[:170],flush=True)
   if attempt==4:raise
   time.sleep(10+attempt*12)
 time.sleep(1.2)
(OUT/"manifest.json").write_text(json.dumps({"title":"15년 직원 월급 동결, 신입과 같은 월급을 준 사장의 최후","tts_model":"gemini-3.8-flash-tts","audio_speed":"1.25x","duration":round(t,4),"clips":result},ensure_ascii=False,indent=2),encoding="utf-8")
(OUT/"concat.txt").write_text("\n".join("file '"+x["file"]+"'" for x in result)+"\n",encoding="utf-8")
proc(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(OUT/"concat.txt"),"-c:a","pcm_s16le",str(OUT/"full.wav")])
print("FINISHED",len(result),round(t,2),flush=True)
