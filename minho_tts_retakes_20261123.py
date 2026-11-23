#!/usr/bin/env python3
import os,base64,wave,time,re,difflib,json,subprocess
from pathlib import Path
from google import genai
from faster_whisper import WhisperModel
LINES=[
 (11,'Orus','근데 너는? 전에 뭐 배운다며?','Junseok age 36, speaks casual Korean to Minho at a Korean pub, playful but sincere. Clearly say 전에, not 저는, and 배운다며, not 배운 다음에. Natural spoken intonation.'),
 (13,'Orus','너 그 말, 3년 전에도 했잖아!','Junseok, friend of Minho, lightly teasing. Clearly say 너 그 말 and 3년 전에도 했잖아.'),
 (15,'Algenib','그러게… 난 지난 3년 동안 뭘 했지?','Minho age 36 in deep reflection walking alone after a night out. Clearly say 뭘 했지, not 뭐랬지. Natural reflective pace.'),
 (20,'Algenib','아, 어렵네. 그냥 나갈 걸 그랬나?','Minho age 36 mildly frustrated while studying alone, quiet natural conversation. Clearly say 나갈 걸 그랬나.'),
 (24,'Orus','야, 요즘 왜 안 보여? 술 끊었냐?','Junseok age 36 teasing his friend Minho, natural easygoing Korean, clearly articulate 술 끊었냐.')
]
out=Path('minho_tts_retakes');out.mkdir(exist_ok=True)
client=genai.Client(http_options={'api_version':'v1beta'},api_key=os.environ['GEMINI_API_KEY'])
asr=WhisperModel('small',device='cpu',compute_type='int8',cpu_threads=4)
def norm(s):return re.sub(r'[^0-9가-힣a-z]','',s.lower())
res=[]
for idx,voice,text,style in LINES:
 good=False
 for attempt in range(5):
  try:
   prompt=style+' No add-ons or preface. Speak EXACTLY the given Korean dialogue, natural volume, warm conversational tone, each ending syllable distinct. No music.'
   response=client.interactions.create(model='gemini-3.8-flash-tts',
    input=[{'type':'user_input','content':[{'type':'text','text':text,'annotations':[{'type':'speech_metadata','style':prompt}]}]}],
    response_format={'type':'audio'},generation_config={'speech_config':[{'voice':voice}]})
   b=response.output_audio.data;blob=base64.b64decode(b) if isinstance(b,str) else b
   raw=out/f'raw_{idx:02d}.wav'
   if blob[:4]==b'RIFF':raw.write_bytes(blob)
   else:
    with wave.open(str(raw),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(blob)
   heard=' '.join(s.text.strip() for s in asr.transcribe(str(raw),language='ko',beam_size=4,condition_on_previous_text=False)[0])
   sim=difflib.SequenceMatcher(None,norm(text),norm(heard),autojunk=False).ratio()
   print('ASR',idx,round(sim,3),heard,flush=True)
   # specific discriminating key phrase required when relevant
   required={11:['전에','배운다'],13:['그 말','3년'],15:['3년','했지'],20:['나갈','그랬'],24:['술','끊']}.get(idx,[])
   if sim<.77 or any(norm(t) not in norm(heard) for t in required):raise ValueError('Wrong read')
   dest=out/f'line_{idx:02d}.wav'
   p=subprocess.run(['ffmpeg','-y','-v','error','-i',str(raw),'-af','loudnorm=I=-18:TP=-1.5:LRA=8,apad=pad_dur=0.18','-ar','24000','-ac','1',str(dest)],capture_output=True,text=True)
   if p.returncode:raise ValueError(p.stderr)
   with wave.open(str(dest)) as w:sec=w.getnframes()/w.getframerate()
   res.append({'index':idx,'voice':voice,'text':text,'asr':heard,'similarity':round(sim,3),'file':dest.name,'seconds':round(sec,3),'attempt':attempt+1})
   good=True;break
  except Exception as e:
   print('RETRY',idx,attempt+1,str(e)[:180],flush=True)
   if attempt==4:raise
   time.sleep(12+attempt*10)
 if not good:raise RuntimeError(f'Retake {idx} failed')
 time.sleep(4)
(out/'manifest.json').write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf8')
print('RETakes_DONE',len(res),flush=True)
