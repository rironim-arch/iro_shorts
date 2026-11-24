from pathlib import Path
import os,time,base64,wave,re,json,difflib,subprocess
from google import genai
from faster_whisper import WhisperModel
LINES=[["hook","열다섯 해를 함께한 까미는, 마지막 순간에도 나를 집까지 데려다주었습니다. 꿈속에서요."],["market","어릴 적 엄마를 따라간 시골 장터. 낡은 종이상자 안에는 강아지 다섯 마리가 있었습니다."],["market","다른 아이들은 서로 장난쳤지만, 유독 까맣고 작은 한 마리만 구석에서 떨고 있었죠."],["market","이상하게 그 아이에게서 눈을 뗄 수 없었습니다."],["market","엄마, 나 저 까만 강아지 데려가면 안 돼?"],["market","그냥… 내가 지켜줘야 할 것 같아."],["naming","그날 작은 강아지를 품에 안고 돌아왔습니다."],["naming","아프지 말고, 까만 털이 꼭 밤하늘 같아서, 이름을 까미라고 지었죠."],["child","그런데 이상한 일이었습니다. 까미가 자랄수록, 나를 지켜주는 건 오히려 까미였습니다."],["school","학교에서 속상한 일이 생겨 혼자 울던 날에는 말없이 곁에 앉아 있었고,"],["road","캄캄한 시골길이 무서울 때면 언제나 내 앞에서 걸어주었습니다."],["gate","늦게 돌아오는 날이면 대문 앞에서 나를 기다렸습니다."],["aging","나는 어느새 어른이 되었고, 까만 까미의 얼굴에도 흰 털이 하나둘 늘었습니다."],["aging","함께한 지 열다섯 해. 까미는 이제 혼자 일어서는 것조차 힘겨워했습니다."],["night","그날 밤, 까미 곁에 이불을 깔고 누웠습니다."],["night","까미야… 오늘은 내가 네 옆에 있을게."],["dream","까미의 등을 쓰다듬다 잠든 나는, 아주 오래전 살던 시골길을 꿈꾸었습니다."],["dream","어두운 길 뒤편에서 익숙한 발소리가 들렸습니다."],["dream","뒤돌아보니, 까미였습니다. 늙고 아픈 모습이 아닌, 젊고 건강한 모습이었죠."],["dream","까미야! 너 여기 있었구나."],["dream","까미는 꼬리를 흔들더니, 어린 시절처럼 내 앞에서 집까지 걸어주었습니다."],["farewell","대문 앞에 도착하자 까미는 멈춰 서서 나를 오래 바라보았습니다."],["farewell","까미야, 안 들어와?"],["farewell","까미는 조용히 꼬리를 흔들고, 빛이 비치는 길로 천천히 걸어갔습니다."],["morning","그 순간 잠에서 깼습니다. 창문으로 아침 햇살이 들어오고 있었습니다."],["morning","그런데 내 곁의 까미는… 더 이상 숨을 쉬지 않았습니다."],["cry","까미야… 내가 널 지켜준다고 생각했는데, 평생 나를 지켜준 건 너였구나."],["cry","마지막 꿈에서까지 날 집에 데려다줘서 고마워."],["heaven","나보다 먼저 가서 기다리게 해서 미안해. 거기선 아프지 말고 마음껏 뛰어놀아."],["heaven","까미야… 우리, 언젠가 천국에서 꼭 다시 만나자."],["end","내가 지켜주려고 데려온 작은 강아지는, 열다섯 해 동안 나의 가장 든든한 친구였습니다."],["cta","이 이야기가 마음에 남으셨다면 구독과 좋아요 부탁드립니다."]]
out=Path("kkami_gemini");out.mkdir(exist_ok=True)
client=genai.Client(http_options={"api_version":"v1beta"},api_key=os.environ["GEMINI_API_KEY"])
asr=WhisperModel("small",device="cpu",compute_type="int8",cpu_threads=4)
def norm(t):return re.sub(r'[^가-힣0-9a-z]','',t.lower())
records=[];start=0
for i,(scene,script) in enumerate(LINES,1):
 for attempt in range(5):
  try:
   instruction="Voice Kore Korean female narrator, calm intimate emotionally authentic Korean storytelling, nostalgic gentle melancholy. Speak like recollection of a beloved dog, with natural pauses and small sadness; never act sobbing or robotic. No extra words. Entire exact text, every final syllable clear. Constant pitch and level. Only text provided."
   r=client.interactions.create(model="gemini-3.8-flash-tts",input=[{"type":"user_input","content":[{"type":"text","text":script,"annotations":[{"type":"speech_metadata","style":instruction}]}]}],response_format={"type":"audio"},generation_config={"speech_config":[{"voice":"Kore"}]})
   audio=r.output_audio.data
   if not audio:raise RuntimeError("empty")
   binary=base64.b64decode(audio) if isinstance(audio,str) else audio
   source=out/f"raw_{i:02}.wav";final=out/f"clip_{i:02}.wav"
   if binary[:4]==b"RIFF":source.write_bytes(binary)
   else:
    with wave.open(str(source),"wb") as w:
     w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(binary)
   p=subprocess.run(["ffmpeg","-y","-v","error","-i",str(source),"-af","loudnorm=I=-18:TP=-1.5:LRA=9,atempo=1.13,apad=pad_dur=0.10","-ar","24000","-ac","1",str(final)],text=True,capture_output=True)
   if p.returncode:raise RuntimeError(p.stderr)
   with wave.open(str(final)) as w:d=w.getnframes()/w.getframerate()
   segments,_=asr.transcribe(str(final),language="ko",word_timestamps=True,beam_size=3,condition_on_previous_text=False)
   words=[{"text":w.word.strip(),"start":round(max(0,w.start),3),"end":round(min(d,w.end),3)} for s in segments for w in (s.words or [])]
   trans=" ".join(w['text'] for w in words)
   ratio=difflib.SequenceMatcher(None,norm(script),norm(trans),autojunk=False).ratio()
   if ratio<(.65 if len(script)>17 else .50):raise RuntimeError(f"ASR {ratio:.2f} {trans}")
   records.append({"i":i,"scene":scene,"text":script,"file":final.name,"start":round(start,3),"end":round(start+d,3),"duration":round(d,3),"words":words,"asr":trans,"match":round(ratio,3)})
   start+=d
   print("OK",i,scene,round(d,2),round(ratio,2),flush=True)
   break
  except Exception as ex:
   print("RETRY",i,attempt,str(ex)[:150],flush=True)
   if attempt==4:raise
   time.sleep(9+7*attempt)
 time.sleep(0.3)
(out/"manifest.json").write_text(json.dumps({"duration":round(start,3),"clips":records},ensure_ascii=False,indent=2),encoding="utf8")
(out/"concat.txt").write_text("\n".join("file '"+r["file"]+"'" for r in records)+"\n",encoding="utf8")
p=subprocess.run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(out/"concat.txt"),"-c:a","pcm_s16le",str(out/"full.wav")],capture_output=True,text=True)
if p.returncode:raise RuntimeError(p.stderr)
print("DONE total",round(start,2),flush=True)
