from pathlib import Path
import json,os,base64,wave,time,subprocess,re,difflib
from google import genai
GROUPS=[{"scene":"hook_market","text":"까미는 마지막 순간에도 나를 지켜주었습니다. 꿈속에서까지요. 어릴 적, 엄마를 따라갔던 시골 장터. 낡은 상자에는 강아지 다섯 마리가 있었어요. 그중 유독 작고 까만 한 마리가 구석에서 떨고 있었습니다."},{"scene":"adopt","text":"엄마, 나 저 까만 강아지 데려가면 안 돼? 이상하게 자꾸 그 아이에게 눈이 갔습니다. 그냥 내가 지켜줘야 할 것 같았거든요. 그날 그 아이를 안고 집에 돌아왔습니다. 까만 털이 밤하늘 같아서, 이름은 까미라고 지었어요."},{"scene":"childhood","text":"그런데 시간이 지나며 알게 됐습니다. 내가 까미를 지켜준 게 아니라, 까미가 나를 지켜주고 있었다는 걸요. 학교에서 속상한 일이 있어 혼자 울던 날, 까미는 조용히 옆에 앉아 있었고, 캄캄한 시골길에서는 늘 내 앞에서 걸어주었습니다."},{"scene":"years","text":"늦게 돌아오는 날이면 대문 앞에서 나를 기다렸습니다. 그렇게 나는 어른이 됐고, 까미의 까만 얼굴에도 흰 털이 하나둘 늘어났죠. 함께한 지 어느덧 열다섯 해. 까미는 이제 혼자 일어서는 것조차 힘겨워했습니다."},{"scene":"night","text":"그날 밤, 까미 옆에 이불을 깔고 누웠습니다. 까미야, 많이 힘들지? 오늘은 내가 옆에 있을게. 까미의 등을 쓰다듬다 나도 모르게 잠들었습니다. 그런데 아주 이상한 꿈을 꾸었어요."},{"scene":"dream","text":"꿈속에서 나는 어린 시절 살던 시골길을 걷고 있었습니다. 뒤에서 익숙한 발소리가 들렸습니다. 돌아보니 까미가 서 있었어요. 늙고 아픈 모습이 아닌, 젊고 건강했던 모습으로 꼬리를 흔들고 있었습니다. 까미야! 너 여기 있었구나!"},{"scene":"farewell","text":"까미는 예전처럼 내 앞에서 걸었습니다. 어두운 길을 지나 집 앞까지 데려다주었죠. 그런데 대문 앞에서 걸음을 멈췄습니다. 까미야, 안 들어와? 까미는 나를 한참 바라보다 꼬리를 살며시 흔들었습니다. 그리고 빛이 비치는 길로 천천히 걸어갔습니다. 까미야! 같이 가야지!"},{"scene":"morning","text":"그 순간 잠에서 깼습니다. 아침 햇살이 들어오고 있었어요. 습관처럼 옆에 누운 까미를 쓰다듬었습니다. 그런데 까미는, 더 이상 숨을 쉬지 않았습니다. 까미야… 까미야, 일어나 봐… 아무리 불러도 눈을 뜨지 않았습니다."},{"scene":"goodbye","text":"어릴 땐 내가 널 지켜준다고 생각했는데, 평생 나를 지켜준 건 너였구나. 마지막 꿈에서까지 집에 데려다줘서 고마워. 나보다 먼저 가서 기다리게 해서 미안해. 거기선 아프지 말고 마음껏 뛰어놀아. 까미야… 우리 언젠가 천국에서 꼭 다시 만나자."},{"scene":"closing","text":"내가 지켜주려고 데려온 작고 약한 강아지. 까미는 열다섯 해 동안 나를 지켜준 가장 든든한 친구였습니다. 이 이야기가 마음에 남으셨다면 구독과 좋아요 부탁드립니다."}]
OUT=Path("kkami_kore_v2");OUT.mkdir(exist_ok=True)
client=genai.Client(http_options={"api_version":"v1beta","timeout":55000},api_key=os.environ["GEMINI_API_KEY"])
records=[]
def norm(s):return re.sub(r"[^가-힣a-z0-9]","",s.lower())
start=0
for i,item in enumerate(GROUPS,1):
 script=item["text"]
 for attempt in range(3):
  try:
   print("REQUEST_START",i,attempt,flush=True)
   response=client.interactions.create(model="gemini-3.8-flash-tts",input=[{"type":"user_input","content":[{"type":"text","text":script,"annotations":[{"type":"speech_metadata","style":"Use Gemini Kore female voice. Authentic Korean woman quietly recalling a dog who was her lifelong friend. Warm lively childhood recollections, quietly worried during aging, gently awed during dream, then heartrending but restrained during goodbye. Realistic conversational Korean, not overly theatrical or announcer voice. Articulate full sentences, no extra words, no music."}]}]}],response_format={"type":"audio"},generation_config={"speech_config":[{"voice":"Kore"}]})
   aud=response.output_audio.data
   if not aud:raise RuntimeError("empty audio data")
   dat=base64.b64decode(aud) if isinstance(aud,str) else aud
   source=OUT/f"raw_{i:02d}.wav"; dest=OUT/f"clip_{i:02d}.wav"
   if dat[:4]==b"RIFF":source.write_bytes(dat)
   else:
    with wave.open(str(source),"wb") as w:
     w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(dat)
   run=subprocess.run(["ffmpeg","-v","error","-y","-i",str(source),"-af","loudnorm=I=-18:TP=-1.5:LRA=9,atempo=1.25,apad=pad_dur=0.10","-ar","24000","-ac","1",str(dest)],capture_output=True,text=True,timeout=45)
   if run.returncode:raise RuntimeError(run.stderr[-300:])
   with wave.open(str(dest)) as w:d=w.getnframes()/w.getframerate()
   if not (3<d<75):raise RuntimeError("invalid duration "+str(d))
   records.append({"i":i,"scene":item["scene"],"text":script,"file":dest.name,"start":round(start,3),"end":round(start+d,3),"duration":round(d,3)})
   start+=d
   print("CLIP_OK",i,round(d,2),"total",round(start,2),flush=True)
   break
  except Exception as ex:
   print("FAIL",i,attempt,type(ex).__name__,str(ex)[:500],flush=True)
   if attempt==2:raise
   time.sleep(4)
(OUT/"manifest.json").write_text(json.dumps({"duration":round(start,3),"clips":records,"voice":"Kore","speed":1.25},ensure_ascii=False,indent=2),encoding="utf8")
(OUT/"concat.txt").write_text("\n".join("file '"+x["file"]+"'" for x in records)+"\n",encoding="utf8")
p=subprocess.run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(OUT/"concat.txt"),"-c:a","pcm_s16le",str(OUT/"full.wav")],capture_output=True,text=True,timeout=45)
if p.returncode:raise RuntimeError(p.stderr)
print("COMPLETE",round(start,2),flush=True)
