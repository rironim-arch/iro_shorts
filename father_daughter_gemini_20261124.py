from pathlib import Path
import os,time,base64,wave,re,json,difflib,subprocess
from google import genai
from faster_whisper import WhisperModel
TURN_LIST=[["n","hook","52살에 직장을 잃은 남자. 해고당한 날에도 울지 않았습니다."],["n","hook","그런데 어느 날, 초등학생 딸의 숙제장을 읽다가 끝내 눈물을 흘렸습니다."],["n","office","김성호 씨는 22년 동안 한 회사에서 일했습니다."],["n","office","가족을 위해 야근도 주말 근무도 마다하지 않았죠."],["n","fired","그러던 어느 날, 회사가 구조조정에 들어갔고, 그도 회사를 떠나야 했습니다."],["w","home","여보, 너무 걱정하지 마. 어떻게든 되겠지."],["f","home","내 나이에 어디서 다시 받아주겠어."],["n","jobsearch","그날부터 성호는 매일 구직 사이트를 뒤졌습니다."],["n","jobsearch","수십 군데 이력서를 냈지만 돌아오는 건 불합격 통보뿐이었습니다."],["n","kitchen","어느덧 실직한 지 석 달. 성호는 낮에는 일자리를 알아보고, 저녁에는 가족의 밥을 차렸습니다."],["d","dinner","아빠! 오늘도 아빠가 밥했어?"],["f","dinner","응, 오늘은 네가 좋아하는 김치볶음밥."],["d","dinner","와! 아빠가 해준 게 제일 맛있어!"],["n","dinner","아이는 웃었지만 성호의 마음은 무거웠습니다."],["f","dinner","내가 지금 이러고 있을 때가 아닌데."],["n","homework","어느 날, 딸의 책상 위에 놓인 숙제장이 눈에 들어왔습니다."],["n","homework","제목은 '요즘 내가 가장 행복한 순간'이었습니다."],["d","letter","예전에는 아빠가 항상 늦게 들어왔다."],["d","letter","친구들은 아빠랑 저녁도 먹고 숙제도 하는데, 우리 아빠는 늘 바빴다."],["d","letter","그런데 요즘은 아빠랑 매일 저녁을 먹는다."],["d","letter","아빠는 자꾸 미안하다고 하지만, 나는 지금이 참 좋다."],["d","letter","아빠가 다시 웃었으면 좋겠다."],["n","tears","성호는 한참 동안 그 자리에서 움직이지 못했습니다."],["n","tears","그는 그동안 직장도 자신감도, 가장으로서의 자존심도 잃었다고 생각했습니다."],["n","tears","하지만 자신이 놓치고 살았던 가족과의 시간은 바로 곁에 있었습니다."],["n","restart","물론 실직이 좋은 일이 된 건 아닙니다. 그는 다음 날에도 이력서를 쓰고 면접을 보러 다녔습니다."],["n","restart","다만 힘든 하루였다고 해서, 하루의 모든 순간까지 불행한 건 아니란 걸 알게 됐죠."],["n","newjob","몇 달 뒤 성호는 작은 회사에서 다시 일을 시작하게 됐습니다."],["n","newjob","첫 출근을 앞둔 저녁, 딸이 물었습니다."],["d","goodbye","아빠, 이제 우리 같이 밥 못 먹어?"],["n","goodbye","성호는 딸을 꼭 안아주었습니다."],["f","goodbye","아니. 이제 아빠가 조금 일찍 올게."],["n","ending","인생에는 오르막도 있고 내리막도 있습니다."],["n","ending","넘어져 봤기에 다시 일어서는 기쁨을 알고, 힘든 날을 지나왔기에 평범한 하루가 소중해집니다."],["n","ending","지금 내리막을 걷고 있어도 너무 슬퍼하지 마세요. 그 길에서도 소중한 것을 발견할 수 있으니까요."],["n","ending","이 이야기가 마음에 남으셨다면 구독과 좋아요 부탁드립니다."]]
OUT=Path("dad_daughter_gemini");OUT.mkdir(exist_ok=True)
client=genai.Client(http_options={"api_version":"v1beta"},api_key=os.environ["GEMINI_API_KEY"])
asr=WhisperModel("small",device="cpu",compute_type="int8",cpu_threads=4)
STYLE={
"n":"Kore female voice. Warm restrained Korean drama narrator, naturally conversational, sensitive and realistic, with subtle emotion and measured gentle pace, never robotic, no theatrics. Perfect Korean articulation. Only say supplied script; no extra sentences.",
"f":"Orus male voice. A Korean father aged 52. Sound mature and realistic, dejected after layoff, gentle around his daughter, quietly sincere, not sobbing or theatrical. Natural everyday spoken Korean and consistent steady volume.",
"w":"Kore female voice as a Korean wife in her late forties comforting her husband with warmth and worry. Natural intimate spoken Korean, not grand theatrical acting.",
"d":"Kore female voice. Try to sound like a cheerful Korean elementary school daughter in a very gentle playful manner, with a slightly light youthful intonation, later thoughtful sincere reading of her own school homework. Avoid cartoonish voice and don't speed up."
}
VOICES={"n":"Kore","f":"Orus","w":"Kore","d":"Kore"}
def norm(s):
 s=s.lower().replace("52","쉰두").replace("22","스물두").replace("3","세")
 return re.sub("[^가-힣a-z0-9]","",s)
def proc(args):
 r=subprocess.run(args,text=True,capture_output=True)
 if r.returncode:raise RuntimeError(r.stderr[-1200:])
result=[];t=0.0
for i,(role,scene,script) in enumerate(TURN_LIST,1):
 for attempt in range(6):
  try:
   resp=client.interactions.create(model="gemini-3.8-flash-tts",input=[{"type":"user_input","content":[{"type":"text","text":script,"annotations":[{"type":"speech_metadata","style":STYLE[role]+" Read the exact Korean words and all last syllables, without titles, commentary or background music."}]}]}],response_format={"type":"audio"},generation_config={"speech_config":[{"voice":VOICES[role]}]})
   a=resp.output_audio.data
   if not a:raise RuntimeError("No audio")
   data=base64.b64decode(a) if isinstance(a,str) else a
   src=OUT/f"raw_{i:02d}.wav"
   if data[:4]==b"RIFF":src.write_bytes(data)
   else:
    with wave.open(str(src),"wb") as w:
     w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(data)
   sped=OUT/f"clip_{i:02d}.wav"
   proc(["ffmpeg","-y","-v","error","-i",str(src),"-af","loudnorm=I=-18:TP=-1.5:LRA=10,atempo=1.25,apad=pad_dur=0.12","-ar","24000","-ac","1",str(sped)])
   with wave.open(str(sped)) as w:duration=w.getnframes()/w.getframerate()
   if not (.6<duration<30):raise RuntimeError("duration "+str(duration))
   segs,info=asr.transcribe(str(sped),language="ko",word_timestamps=True,beam_size=4,condition_on_previous_text=False,vad_filter=False)
   words=[];heard=[]
   for seg in segs:
    for v in seg.words or []:
     words.append({"text":v.word.strip(),"start":max(0,round(v.start,3)),"end":min(duration,round(v.end,3)),"probability":round(v.probability,3)})
     heard.append(v.word.strip())
   spoken=" ".join(heard)
   match=difflib.SequenceMatcher(None,norm(script),norm(spoken),autojunk=False).ratio()
   if match<(.66 if len(norm(script))>14 else .55) or len(norm(spoken))<.63*len(norm(script)):
    raise RuntimeError("ASR mismatch "+str(round(match,2))+" "+spoken)
   record={"i":i,"role":role,"scene":scene,"text":script,"voice":VOICES[role],"file":sped.name,"start":round(t,4),"end":round(t+duration,4),"duration":round(duration,4),"words":words,"asr":spoken,"asr_match":round(match,3)}
   print("PASSED",i,scene,VOICES[role],round(duration,2),round(match,2),flush=True)
   result.append(record);t+=duration
   break
  except Exception as e:
   print("RETRY",i,attempt+1,str(e)[:170],flush=True)
   if attempt==5:raise
   time.sleep(10+attempt*10)
 time.sleep(1)
(OUT/"manifest.json").write_text(json.dumps({"title":"52세에 실직한 아버지가 딸의 숙제를 보고 울었던 이유","tts_model":"gemini-3.8-flash-tts","audio_speed":"1.25x","duration":round(t,4),"clips":result},ensure_ascii=False,indent=2),encoding="utf-8")
(OUT/"concat.txt").write_text("\n".join("file '"+x["file"]+"'" for x in result)+"\n",encoding="utf-8")
proc(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(OUT/"concat.txt"),"-c:a","pcm_s16le",str(OUT/"full.wav")])
print("FINISHED",len(result),round(t,2),flush=True)
