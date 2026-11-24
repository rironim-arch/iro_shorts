from pathlib import Path
import os,time,base64,wave,re,json,difflib,subprocess
from google import genai
from faster_whisper import WhisperModel
# Separate long-form draft; no YouTube publishing.
DRAFT="""1|n|새벽 다섯 시였습니다. 모두가 잠들어 있던 골목에서 대문을 긁는 소리가 들렸습니다. 잠에서 깬 지연 씨가 외투를 걸치고 문을 열었습니다. 문 앞에는 평소 지연 씨가 그토록 싫어했던 옆집 고양이, 나비가 있었습니다.
1|j|너 또 왔니? 이 시간에 무슨 일이야. 집으로 가.
1|n|문을 닫고 돌아서자 다시 긁는 소리가 들렸습니다. 이상하게도 녀석은 그날따라 아무리 쫓아내도 떠나지 않았습니다. 지연 씨가 결국 대문 밖으로 나왔을 때, 나비는 골목 끝으로 달려갔다가 다시 돌아왔습니다. 마치 따라오라는 듯이 말이죠. 그날 새벽, 지연 씨는 고양이를 따라간 일이 자신의 인생에서 가장 잘한 선택 중 하나였다고 말하게 됩니다.
2|n|이야기는 일 년 전으로 돌아갑니다. 오래된 주택들이 모여 있는 이 골목에는 일흔두 살 순자 할머니가 살고 있었습니다. 남편을 먼저 보내고, 외아들은 멀리 떨어진 도시에서 직장 생활을 하고 있었죠. 할머니는 아침이면 화분에 물을 주고 시장에 다녀왔습니다. 장을 보고 돌아와서는 혼자 먹을 만큼만 밥을 지었습니다. 남편과 함께 쓰던 식탁에는 이제 의자 하나만 사용하고 있었습니다. 저녁이면 텔레비전을 켜두었습니다. 딱히 보고 싶은 프로그램이 있어서가 아니라 집 안에 사람 목소리가 들리는 것이 좋았기 때문입니다.
3|n|어느 늦가을, 비가 유난히 많이 내리던 날이었습니다. 장바구니를 들고 돌아오던 할머니의 귀에 작은 울음소리가 들렸습니다. 담벼락 아래에는 어린 고양이 한 마리가 흠뻑 젖은 채 웅크리고 있었습니다. 한쪽 다리를 제대로 딛지 못했습니다.
3|g|아이고, 너 어쩌다가 이런 데까지 왔니. 엄마는 어디 갔어?
3|n|할머니가 가까이 다가가자 녀석은 겁에 질려 몸을 움츠렸습니다. 할머니는 한 발짝 물러서서 우산을 고양이 쪽으로 기울였습니다. 집에서 마른 수건을 가져와 녀석 옆에 내려놓고 기다렸습니다. 한참 뒤에야 고양이를 조심스럽게 품에 안을 수 있었습니다.
3|g|괜찮아. 이제 비 안 맞아도 돼.
4|n|다음 날 할머니는 고양이를 동물병원에 데려갔습니다. 치료비가 적지 않았지만 할머니는 녀석을 다시 길에 내보낼 생각은 하지 않았습니다. 집으로 돌아온 할머니는 작은 상자에 담요를 깔아주고 물과 밥을 챙겼습니다. 고양이는 이틀 동안 상자 밖으로 거의 나오지 않았습니다. 할머니가 조금씩 떨어져 앉아 기다리자, 사흘째 되던 날 녀석이 먼저 다가왔습니다.
4|g|그래, 이제 좀 살 만하니? 우리 나비라고 부를까?
4|n|그렇게 나비는 할머니의 가족이 되었습니다.
5|n|그런데 나비의 등장으로 불편해진 사람이 있었습니다. 옆집에 사는 지연 씨였습니다. 지연 씨는 새벽에 출근하고 저녁 늦게 돌아오는 생활을 하고 있었고, 집에서만큼은 조용히 쉬고 싶었습니다. 어느 날 나비가 열린 문으로 나와 지연 씨의 마당에 들어갔다가 화분을 넘어뜨렸습니다.
5|j|어르신, 고양이 좀 잘 봐주세요. 이거 보세요. 화분이 다 깨졌잖아요.
5|g|어머, 내가 몰랐네. 정말 미안해요. 얼른 치울게요.
5|j|제가 치울 테니까 다음부터는 못 나오게 해주세요.
5|n|할머니는 다음 날 부침개를 만들어 옆집에 가져갔습니다.
5|g|어제 미안해서 조금 부쳤어요. 따뜻할 때 먹어요.
5|j|괜찮아요. 저 곧 나가야 해서요.
5|n|문이 닫히고 할머니는 접시를 들고 돌아왔습니다. 그날 할머니는 현관의 작은 반려동물 출입문을 점검하고 바깥 대문 틈도 막았습니다. 나비가 이웃집에 가지 않게 더 신경을 쓰기 시작했습니다.
6|n|계절이 바뀌면서 나비는 제법 큰 고양이가 되었습니다. 할머니가 눈을 뜨면 침대 옆에 있었고, 시장에서 돌아오는 발소리가 들리면 현관에서 기다렸습니다. 할머니는 어느새 나비에게 하루 동안 있었던 일을 하나하나 이야기했습니다.
6|g|오늘은 두부가 싸더라. 두 모나 샀어. 너는 네 밥 먹어야지. 그건 할미 거야.
6|n|나비가 식탁 위를 기웃거리면 할머니는 웃으며 내려주었습니다. 빨래를 개고 있으면 나비는 꼭 깨끗한 빨래 위에 올라가 앉았습니다. 그럴 때마다 할머니는 못 이기는 척 웃었습니다. 텔레비전 소리로 채우던 집에 이제는 할머니의 웃음소리가 들렸습니다.
7|s|엄마, 미안해. 이번 주는 회사 일이 밀려서 내려가기 어려울 것 같아.
7|g|그래. 일부터 해야지. 다음에 와.
7|s|병원은 다녀왔어? 혼자 괜찮지?
7|g|걱정하지 마. 엄마 요즘 혼자 아니야. 나비가 얼마나 웃기는지 몰라.
7|n|전화를 끊고 할머니는 잠시 창밖을 바라보았습니다. 아들이 나쁜 사람이라고 생각하지 않았습니다. 그 아이에게도 먹고살아야 할 일이 있다는 것을 잘 알았습니다. 그렇지만 보고 싶은 마음이 없어지는 것은 아니었죠. 나비가 할머니의 무릎으로 올라왔습니다.
7|g|너는 할미랑 오래오래 살자. 어디 아프지 말고.
8|n|그러던 어느 겨울날, 할머니는 몸이 평소와 다르다는 것을 느꼈습니다. 시장에서 돌아오는 길에 어지러워 몇 번이나 멈춰 섰습니다. 마침 옆집 지연 씨와 마주쳤습니다.
8|j|어르신, 얼굴이 좀 안 좋아 보이는데요. 어디 아프세요?
8|g|괜찮아요. 장을 좀 많이 봤더니 힘이 드나 봐.
8|j|너무 무리하지 마세요.
8|n|지연 씨는 출근 시간에 쫓기고 있었습니다. 잠깐 할머니의 장바구니를 바라보다 자신의 집으로 들어갔습니다. 할머니도 별일 아니겠거니 생각했습니다. 그때만 해도 두 사람 모두 그날 저녁에 무슨 일이 벌어질지 알지 못했습니다.
9|n|저녁이 되자 할머니는 나비에게 밥을 챙겨주려고 일어났습니다.
9|g|아이고, 우리 나비 밥도 아직 안 줬네. 잠깐만 기다려.
9|n|사료를 꺼내려던 순간 할머니는 식탁을 붙잡았습니다. 다리에 힘이 빠지고 눈앞이 흐려졌습니다. 그리고 그대로 바닥에 쓰러졌습니다. 나비가 다가와 할머니의 손에 코를 대고 울었습니다. 평소라면 울음소리를 들은 할머니가 바로 돌아보았을 텐데, 그날은 아무런 반응이 없었습니다. 텔레비전 소리만 거실에 흐르고 있었습니다. 밤이 깊어졌습니다. 나비는 할머니의 곁을 서성였습니다. 그러다 현관 쪽으로 향했습니다. 바람에 조금 벌어진 마당 쪽 문과 대문 아래의 좁은 틈을 지나 골목으로 나갔습니다.
10|n|그리고 새벽 다섯 시. 지연 씨의 대문 앞이었습니다.
10|j|나비야, 나 이제 좀 자자. 왜 이러니 정말.
10|n|지연 씨는 문을 닫으려다가 멈췄습니다. 나비는 문을 긁고 몇 걸음씩 옆집 쪽으로 달려갔다가 돌아왔습니다. 평소 지연 씨를 보면 피하던 고양이였습니다. 그런데 그날은 가까이 와서 바짓자락을 건드리고 울었습니다.
10|j|뭐가 있는 거야? 어디 가자는 거니?
10|n|지연 씨는 할머니의 집 쪽으로 따라갔습니다. 대문 앞에서 할머니를 불렀습니다.
10|j|어르신! 저 옆집인데요. 안에 계세요?
10|n|대답이 없었습니다. 여러 번 문을 두드려도 아무 소리도 들리지 않았습니다. 이상하게 켜져 있는 거실 불빛과 계속 울어대는 나비를 보고, 지연 씨는 문득 전날 시장에서 만났던 할머니의 창백한 얼굴을 떠올렸습니다. 지연 씨는 휴대전화를 꺼내 119에 신고했습니다.
11|n|구급대원이 도착하고 집 안을 확인했습니다. 거실 바닥에는 순자 할머니가 쓰러져 있었습니다. 지연 씨는 순간 말문이 막혔습니다. 만약 조금 전처럼 문을 닫아버렸다면 어땠을까. 그 생각이 떠오르자 다리에 힘이 빠졌습니다. 할머니는 응급처치를 받고 병원으로 이송됐습니다. 나비는 현관 앞에서 구급대원들의 모습을 지켜보다 구급차가 떠나는 쪽으로 몇 걸음 따라갔습니다.
11|j|너, 그래서 나한테 온 거였어?
11|n|지연 씨는 고양이 앞에 쪼그려 앉았습니다. 손을 내밀었지만 나비는 구급차가 사라진 쪽만 바라보았습니다.
12|n|병원에서 치료받은 할머니는 다행히 의식을 되찾았습니다. 연락을 받고 달려온 아들이 어머니의 손을 잡았습니다.
12|s|엄마, 나야. 괜찮아? 나 보여?
12|g|왔니? 그런데 우리 나비는?
12|s|옆집 분이 보고 계신대. 걱정하지 마. 엄마 몸부터 생각해.
12|g|밥도 못 줬는데. 그 녀석 배고플 텐데.
12|n|아들은 잠시 고개를 숙였습니다. 어머니가 그 고양이에게 얼마나 의지하고 있었는지 그제야 조금 알 것 같았습니다. 아들은 지연 씨에게 전화해 감사 인사를 전했습니다.
13|n|지연 씨는 할머니가 입원해 있는 동안 나비의 밥을 챙기기로 했습니다. 사료를 어디에 두어야 하는지도 몰라 인터넷을 찾아보았습니다. 물그릇을 놓고 작은 담요도 꺼냈습니다. 그런데 나비는 밥을 먹으면 다시 할머니의 대문으로 갔습니다. 하루가 지나고 이틀이 지나도 같은 자리였습니다. 비가 내리던 날 지연 씨는 우산을 들고 나왔습니다.
13|j|오늘도 아직 안 오셔. 비 맞으면 안 되잖아. 일단 우리 집에 가자.
13|n|지연 씨가 조심스럽게 손을 내밀자 나비가 손등에 코를 가까이 댔습니다. 지연 씨는 처음으로 녀석의 머리를 쓰다듬었습니다. 처음에는 그저 성가시기만 했던 작은 고양이가 이제는 누군가를 기다리는 가족처럼 보였습니다.
14|n|며칠 뒤 할머니가 퇴원했습니다. 아들의 부축을 받으며 골목으로 들어오는 할머니를 발견한 나비가 달려갔습니다. 할머니는 의자에 앉아 나비를 조심스럽게 품에 안았습니다.
14|g|아이고, 우리 나비. 할미 기다렸어? 미안하다.
14|j|어르신, 이 녀석 덕분에 제가 알았어요. 그날 새벽에 제 대문을 얼마나 긁던지요. 제가 처음에는 그냥 쫓아냈거든요. 그런데 자꾸 돌아오더라고요.
14|g|얘가 그랬다고요?
14|j|네. 안 따라갔으면 어쩔 뻔했나 싶어요.
14|n|할머니는 한동안 아무 말도 하지 못했습니다. 나비의 등을 천천히 쓰다듬었습니다.
14|g|할미가 너를 살린 줄 알았는데…… 네가 할미를 살렸네.
15|n|그 뒤로 두 집 사이에는 작은 변화가 생겼습니다. 지연 씨는 출근길에 할머니에게 안부를 물었고, 무거운 장바구니를 보면 대신 들어주었습니다. 할머니도 반찬을 만들 때면 옆집 몫을 조금 덜어놓았습니다. 예전에는 굳게 닫혀 있던 지연 씨의 대문도 할머니가 찾아오면 반갑게 열렸습니다. 어느 봄날, 두 사람은 할머니의 마당에 의자를 놓고 나란히 앉았습니다.
15|g|지연 씨, 고양이 싫어한다면서요.
15|j|그러게요. 나비한테 제대로 졌네요.
15|n|두 사람이 웃는 사이 나비는 햇볕이 가장 잘 드는 자리를 골라 누웠습니다. 그날 새벽 나비가 어떤 생각으로 대문을 긁었는지는 누구도 정확히 알 수 없습니다. 다만 비에 젖어 떨고 있던 작은 생명을 외면하지 않았던 할머니의 친절이, 전혀 예상하지 못한 모습으로 돌아왔습니다. 그리고 무심했던 이웃에게도 새로운 가족 같은 인연을 만들어주었습니다. 오늘도 할머니의 마당에는 두 개의 의자가 놓여 있습니다. 그 사이에는 나비가 편안히 잠들어 있습니다. 오늘 이야기가 마음에 남으셨다면 구독과 좋아요 부탁드립니다."""
OUT=Path(os.environ["NABI_OUT"]);OUT.mkdir(parents=True,exist_ok=True)
client=genai.Client(http_options={"api_version":"v1beta","timeout":90000,"retry_options":{"attempts":1}},api_key=os.environ["GEMINI_API_KEY"])
asr=WhisperModel("small",device="cpu",compute_type="int8",cpu_threads=4)
STYLE={
"n":"Warm restrained Korean female drama narrator, consistent moderate conversational pace, clear for senior listeners, about 4 to 5 Hangul syllables per second, no sudden accelerations, exaggerated pauses or theatrical emotion.",
"g":"A warm Korean grandmother aged 72, natural mature feminine everyday voice, clear unhurried articulation but never artificially slow, no exaggerated tremor. Tender and quietly sincere.",
"j":"Korean woman in her fifties, natural mature everyday conversation, clear steady rhythm, realistic restrained annoyance or concern depending on words, no shouting or overacting.",
"s":"Mature Korean adult son, everyday conversation, restrained warmth, clear steady pronunciation."
}
VOICES={"n":"Kore","g":"Gacrux","j":"Sulafat","s":"Orus"}
def norm(s):
 return re.sub("[^가-힣a-z0-9]","",s.lower().replace("119","일일구"))
def proc(args):
 subprocess.run(args,check=True,stdout=subprocess.DEVNULL,timeout=25)
def split_paragraph(text):
 sentences=re.split(r"(?<=[.!?])\s+",text)
 chunks=[];cur=""
 for s in sentences:
  if cur and len(cur)+len(s)>240:
   chunks.append(cur);cur=""
  cur=(cur+" "+s).strip()
 if cur:chunks.append(cur)
 return chunks
turns=[]
for row in DRAFT.splitlines():
 scene,role,text=row.split("|",2)
 for chunk in split_paragraph(text):turns.append((int(scene),role,chunk))
assert len(turns)==69, len(turns)
lo,hi=map(int,os.environ["NABI_RANGE"].split("-"))
assert 29<=lo<=hi<=69
result=[];t=0.0
failed=[]
def save_manifest():
 (OUT/"manifest.json").write_text(json.dumps({"title":"고양이의 보은 – 나비","tts_model":"gemini-3.8-flash-tts","duration":round(t,4),"clips":result,"complete":len(result)==hi-lo+1,"expected_clips":hi-lo+1,"range":[lo,hi],"failed":failed},ensure_ascii=False,indent=2),encoding="utf-8")
for i,(scene,role,script) in enumerate(turns,1):
 if not lo<=i<=hi:continue
 for attempt in range(1):
  try:
   print("TTS START",i,flush=True)
   resp=client.interactions.create(model="gemini-3.8-flash-tts",input=[{"type":"user_input","content":[{"type":"text","text":script,"annotations":[{"type":"speech_metadata","style":STYLE[role]+" Read every supplied Korean word and ending exactly, no other words or sound effects. Maintain the same conversational pace throughout."}]}]}],response_format={"type":"audio"},generation_config={"speech_config":[{"voice":VOICES[role]}]})
   print("TTS RETURN",i,flush=True)
   a=resp.output_audio.data
   if not a:raise RuntimeError("No audio")
   data=base64.b64decode(a) if isinstance(a,str) else a
   src=OUT/f"raw_{i:03d}.wav"
   if data[:4]==b"RIFF":src.write_bytes(data)
   else:
    with wave.open(str(src),"wb") as w:
     w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(data)
   sped=OUT/f"clip_{i:03d}.wav"
   rate=1.05 if role=="n" else 1.0
   proc(["ffmpeg","-y","-v","error","-i",str(src),"-af",f"loudnorm=I=-18:TP=-1.5:LRA=10,atempo={rate},apad=pad_dur=0.18","-ar","24000","-ac","1",str(sped)])
   with wave.open(str(sped)) as w:duration=w.getnframes()/w.getframerate()
   if not (.5<duration<100):raise RuntimeError("duration "+str(duration))
   print("ASR START",i,flush=True)
   segs,info=asr.transcribe(str(sped),language="ko",word_timestamps=True,beam_size=4,condition_on_previous_text=False,vad_filter=False)
   words=[];heard=[]
   for seg in segs:
    for v in seg.words or []:
     words.append({"text":v.word.strip(),"start":max(0,round(v.start,3)),"end":min(duration,round(v.end,3)),"probability":round(v.probability,3)})
     heard.append(v.word.strip())
   spoken=" ".join(heard)
   match=difflib.SequenceMatcher(None,norm(script),norm(spoken),autojunk=False).ratio()
   if match<(.72 if len(norm(script))>30 else .55):raise RuntimeError("ASR mismatch "+str(round(match,2)))
   rec={"i":i,"role":role,"scene":scene,"text":script,"voice":VOICES[role],"file":sped.name,"start":round(t,4),"end":round(t+duration,4),"duration":round(duration,4),"words":words,"asr":spoken,"asr_match":round(match,3)}
   result.append(rec);t+=duration;save_manifest()
   print("PASSED",i,"of",len(turns),scene,VOICES[role],round(duration,2),round(match,2),flush=True)
   break
  except Exception as e:
   print("RETRY",i,attempt+1,type(e).__name__,str(e)[:160],flush=True)
   if attempt==0:
    failed.append({"i":i,"error":str(e)[:240]});save_manifest();break
   time.sleep(6+attempt*10)
 time.sleep(1)
save_manifest()
print("BATCH FINISHED",lo,hi,len(result),failed,flush=True)
if failed: raise SystemExit(1)
