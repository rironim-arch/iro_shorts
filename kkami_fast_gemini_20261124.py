from pathlib import Path
import os,sys,time,base64,json,wave,subprocess,re
from google import genai
GROUPS=[{"scene":"market","text":"열다섯 해를 함께한 까미는, 마지막 순간에도 나를 집까지 데려다주었습니다. 꿈속에서요. 어릴 적 엄마를 따라간 시골 장터. 낡은 종이상자 안에는 강아지 다섯 마리가 있었습니다. 다른 아이들은 서로 장난쳤지만, 유독 까맣고 작은 한 마리만 구석에서 떨고 있었죠."},{"scene":"market","text":"이상하게 그 아이에게서 눈을 뗄 수 없었습니다. 엄마, 나 저 까만 강아지 데려가면 안 돼? 그냥… 내가 지켜줘야 할 것 같아."},{"scene":"child","text":"그날 작은 강아지를 품에 안고 돌아왔습니다. 아프지 말고, 까만 털이 꼭 밤하늘 같아서, 이름을 까미라고 지었죠. 그런데 이상한 일이었습니다. 까미가 자랄수록, 나를 지켜주는 건 오히려 까미였습니다."},{"scene":"gate","text":"학교에서 속상한 일이 생겨 혼자 울던 날에는 말없이 곁에 앉아 있었고, 캄캄한 시골길이 무서울 때면 언제나 내 앞에서 걸어주었습니다. 늦게 돌아오는 날이면 대문 앞에서 나를 기다렸습니다."},{"scene":"night","text":"나는 어느새 어른이 되었고, 까만 까미의 얼굴에도 흰 털이 하나둘 늘었습니다. 함께한 지 열다섯 해. 까미는 이제 혼자 일어서는 것조차 힘겨워했습니다. 그날 밤, 까미 곁에 이불을 깔고 누웠습니다."},{"scene":"dream","text":"까미야… 오늘은 내가 네 옆에 있을게. 까미의 등을 쓰다듬다 잠든 나는, 아주 오래전 살던 시골길을 꿈꾸었습니다. 어두운 길 뒤편에서 익숙한 발소리가 들렸습니다."},{"scene":"dream","text":"뒤돌아보니, 까미였습니다. 늙고 아픈 모습이 아닌, 젊고 건강한 모습이었죠. 까미야! 너 여기 있었구나. 까미는 꼬리를 흔들더니, 어린 시절처럼 내 앞에서 집까지 걸어주었습니다."},{"scene":"farewell","text":"대문 앞에 도착하자 까미는 멈춰 서서 나를 오래 바라보았습니다. 까미야, 안 들어와? 까미는 조용히 꼬리를 흔들고, 빛이 비치는 길로 천천히 걸어갔습니다."},{"scene":"cry","text":"그 순간 잠에서 깼습니다. 창문으로 아침 햇살이 들어오고 있었습니다. 그런데 내 곁의 까미는… 더 이상 숨을 쉬지 않았습니다. 까미야… 내가 널 지켜준다고 생각했는데, 평생 나를 지켜준 건 너였구나."},{"scene":"heaven","text":"마지막 꿈에서까지 날 집에 데려다줘서 고마워. 나보다 먼저 가서 기다리게 해서 미안해. 거기선 아프지 말고 마음껏 뛰어놀아. 까미야… 우리, 언젠가 천국에서 꼭 다시 만나자."},{"scene":"cta","text":"내가 지켜주려고 데려온 작은 강아지는, 열다섯 해 동안 나의 가장 든든한 친구였습니다. 이 이야기가 마음에 남으셨다면 구독과 좋아요 부탁드립니다."}]
out=Path('kkami_fast');out.mkdir(exist_ok=True)
client=genai.Client(http_options={"api_version":"v1beta"},api_key=os.environ['GEMINI_API_KEY'])
records=[];t=0
for i,g in enumerate(GROUPS,1):
 for attempt in range(4):
  try:
   response=client.interactions.create(model='gemini-3.8-flash-tts',input=[{'type':'user_input','content':[{'type':'text','text':g['text'],'annotations':[{'type':'speech_metadata','style':'Kore female warm Korean storyteller, calm restrained tender and wistful. No artificial emotion. Speak the complete Korean lines clearly with a natural medium pace. No extra words, no music.'}]}]}],response_format={'type':'audio'},generation_config={'speech_config':[{'voice':'Kore'}]})
   a=response.output_audio.data
   if not a:raise RuntimeError('No audio data')
   dat=base64.b64decode(a) if isinstance(a,str) else a
   orig=out/f'raw_{i:02d}.wav';dst=out/f'clip_{i:02d}.wav'
   if dat[:4]==b'RIFF':orig.write_bytes(dat)
   else:
    with wave.open(str(orig),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000);f.writeframes(dat)
   cmd=['ffmpeg','-v','error','-y','-i',str(orig),'-af','loudnorm=I=-18:TP=-1.5:LRA=10,atempo=1.10,apad=pad_dur=0.1','-ac','1','-ar','24000',str(dst)]
   p=subprocess.run(cmd,capture_output=True,text=True)
   if p.returncode:raise RuntimeError(p.stderr)
   with wave.open(str(dst)) as f:d=f.getnframes()/f.getframerate()
   if d<=2 or d>55:raise RuntimeError('Invalid duration '+str(d))
   # timestamps estimated from the written script for subtitle alignment, improve later with original ASR job if available.
   src=g['text']
   parts=re.split(r'(?<=[.!?。])\s+|(?<=[…])\s+',src);parts=[p for p in parts if p]
   chunks=[];ratio=0;total=sum(len(x) for x in parts)
   for part in parts:
    begin=ratio/total*d;ratio+=len(part);end=ratio/total*d
    chunks.append({'text':part,'start':round(begin,3),'end':round(end,3)})
   records.append({'i':i,'scene':g['scene'],'text':src,'file':dst.name,'start':round(t,3),'end':round(t+d,3),'duration':round(d,3),'words':[{'text':p['text'],'start':p['start'],'end':p['end']} for p in chunks]})
   t+=d
   print('DONE',i,round(d,2),flush=True)
   break
  except Exception as e:
   print('RETRY',i,attempt,str(e)[:200],flush=True)
   if attempt==3:raise
   time.sleep(8+attempt*8)
(out/'manifest.json').write_text(json.dumps({'duration':round(t,3),'clips':records},ensure_ascii=False,indent=2))
(out/'concat.txt').write_text('\n'.join("file '"+c['file']+"'" for c in records)+'\n')
p=subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(out/'concat.txt'),'-c:a','pcm_s16le',str(out/'full.wav')],capture_output=True,text=True)
if p.returncode:raise RuntimeError(p.stderr)
print('TOTAL',round(t,2),flush=True)
