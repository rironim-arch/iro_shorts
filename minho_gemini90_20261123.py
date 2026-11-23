#!/usr/bin/env python3
import os,time,re,base64,wave,subprocess,json,difflib,concurrent.futures
from pathlib import Path
from google import genai
from faster_whisper import WhisperModel
TURNS=[["n","친구들과 있을 땐 즐거운데, 집에 돌아오면 왜 더 외로울까요?"],["f","야 민호야! 내일도 모이는데 올 거지?"],["m","당연하지! 나 빼고 놀지 마!"],["n","금요일엔 술자리, 주말엔 또 모임. 서른여섯 민호의 일상이었습니다."],["n","하지만 집에 돌아오면 웃음은 금세 사라졌죠."],["m","분명 재밌었는데… 왜 이렇게 허전하지?"],["n","외로울 때마다 다음 약속을 잡았습니다. 혼자 시간을 채우는 습관이 없었거든요."],["n","그렇게 비슷한 주말이 3년이나 흘렀습니다."],["f","야, 나 자격증 땄어! 다음 달부터 새 회사 가!"],["m","와, 축하한다! 진짜 열심히 하더니."],["f","근데 너는? 전에 뭐 배운다며?"],["m","아… 나도 이제 시작하려고."],["f","너 그 말, 3년 전에도 했잖아!"],["n","웃었지만 집에 가는 내내 그 말이 떠올랐습니다."],["m","그러게… 난 지난 3년 동안 뭘 했지?"],["n","사진첩엔 술자리 사진뿐. 공부와 운동은 늘 미뤘죠."],["f","야, 오늘도 한잔하자!"],["m","미안, 오늘은 못 가. 나도 뭐 하나 시작하려고."],["n","그날 민호는 미뤄둔 강의를 틀었습니다."],["m","아, 어렵네. 그냥 나갈 걸 그랬나?"],["n","그래도 휴대전화를 내려놓고 다시 책을 폈습니다."],["n","퇴근 후엔 공부하고, 주말엔 가볍게 뛰었습니다."],["n","한 달 뒤, 드디어 강의 하나를 끝냈습니다."],["f","야, 요즘 왜 안 보여? 술 끊었냐?"],["m","아니, 너희도 만나야지. 근데 나한테도 시간을 좀 쓰려고."],["n","외로움은 여전했습니다. 다만 혼자 있는 시간을 채울 습관이 생겼습니다."],["n","이 이야기가 마음에 남으셨다면 구독과 좋아요 부탁드립니다."]]
VOICES={'n':'Kore','m':'Algenib','f':'Orus'}
STYLES={
'n':'Warm natural Korean female storytelling voice, about age 40. Consistent unhurried tempo, cinematic realistic narration and subtle emotional change. Never overact. No background music.',
'm':'Minho, 36-year-old Korean male ordinary slightly overweight office worker. Speak like a real friend, not an actor performing a commercial. Subtly cheerful at parties, slightly sad alone, later hopeful. Natural Korean conversation. No background music.',
'f':'Junseok, 36-year-old Korean male friend. Friendly informal Korean speech, gently teasing without cruelty, naturally excited about his certificate, no overacting. No background music.'
}
OUT=Path("minho_gemini90_result");OUT.mkdir(exist_ok=True)
client=genai.Client(http_options={'api_version':'v1beta'},api_key=os.environ['GEMINI_API_KEY'])
asr=WhisperModel('base',device='cpu',compute_type='int8',cpu_threads=4)
def norm(s):return re.sub(r'[^0-9가-힣a-z]','',s.lower())
def sh(a):
 p=subprocess.run(a,capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stderr[-500:])
def generate(item):
 i,role,line=item; dest=OUT/f'line_{i:02d}.wav'
 for attempt in range(4):
  try:
   response=client.interactions.create(
    model='gemini-3.8-flash-tts',
    input=[{'type':'user_input','content':[{'type':'text','text':line,'annotations':[{'type':'speech_metadata','style':STYLES[role]+' Speak exactly this sentence, with every last Korean syllable complete, no added words or role labels. Stable natural speed and volume.'}]}]}],
    response_format={'type':'audio'},generation_config={'speech_config':[{'voice':VOICES[role]}]})
   blob=response.output_audio.data
   if not blob:raise ValueError('No TTS audio')
   data=base64.b64decode(blob) if isinstance(blob,str) else blob
   src=OUT/f'raw_{i:02d}.wav'
   if data[:4]==b'RIFF':src.write_bytes(data)
   else:
    with wave.open(str(src),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000);f.writeframes(data)
   with wave.open(str(src)) as f:duration=f.getnframes()/f.getframerate()
   if not .5<duration<28:raise ValueError('Wrong duration '+str(duration))
   heard=' '.join(s.text.strip() for s in asr.transcribe(str(src),language='ko',beam_size=3,condition_on_previous_text=False)[0])
   sim=difflib.SequenceMatcher(None,norm(line),norm(heard),autojunk=False).ratio()
   if sim<.55 or len(norm(heard))<.63*len(norm(line)):raise ValueError('TTS wrong text '+heard)
   sh(['ffmpeg','-y','-hide_banner','-v','error','-i',str(src),'-af','loudnorm=I=-18:TP=-1.5:LRA=8,apad=pad_dur=0.18','-ar','24000','-ac','1',str(dest)])
   with wave.open(str(dest)) as f:duration=f.getnframes()/f.getframerate()
   print('PASS',i,VOICES[role],round(duration,2),round(sim,2),flush=True)
   return {'index':i,'role':role,'text':line,'voice':VOICES[role],'file':dest.name,'seconds':round(duration,3),'asr':heard,'similarity':round(sim,3)}
  except Exception as e:
   print('RETRY',i,attempt+1,str(e)[:170],flush=True)
   if attempt==3:raise
   time.sleep(14+attempt*12)
# Serial avoid TTS limits, but maintain consistent voice and ASR verification.
results=[]
for i,(r,t) in enumerate(TURNS,1):
 results.append(generate((i,r,t)))
 time.sleep(5)
def stamp(t):
 ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
 return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'
seconds=0;srt=[];concat=[]
for i,r in enumerate(results,1):
 srt.append(f"{i}\n{stamp(seconds)} --> {stamp(seconds+r['seconds'])}\n{r['text']}\n")
 seconds+=r['seconds']; concat.append("file '"+r['file']+"'")
(OUT/'captions.srt').write_text('\n'.join(srt),encoding='utf8')
(OUT/'concat.txt').write_text('\n'.join(concat)+'\n',encoding='utf8')
sh(['ffmpeg','-y','-hide_banner','-v','error','-f','concat','-safe','0','-i',str(OUT/'concat.txt'),'-c:a','pcm_s16le',str(OUT/'full.wav')])
sh(['ffmpeg','-y','-hide_banner','-v','error','-i',str(OUT/'full.wav'),'-c:a','libmp3lame','-b:a','128k',str(OUT/'full.mp3')])
(OUT/'manifest.json').write_text(json.dumps({'model':'gemini-3.8-flash-tts','voices':VOICES,'total_seconds':round(seconds,3),'turns':results},ensure_ascii=False,indent=2),encoding='utf8')
print('DONE',len(results),'duration',seconds,flush=True)
