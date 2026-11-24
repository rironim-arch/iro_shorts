from pathlib import Path
import os,json,wave
from openai import OpenAI
files=[]
for i in [1,2,3,4,5,7,8,9,10]:
 folder=Path('trims')/str(i) if i<=5 else Path('batches')/str((i-1)//2)
 files.append(next(folder.rglob(f'clip_{i:02d}.wav')))
with wave.open('kkami_voice_joined.wav','wb') as out:
 out.setnchannels(1);out.setsampwidth(2);out.setframerate(24000)
 for p in files:
  with wave.open(str(p),'rb') as f:
   if f.getnchannels()!=1 or f.getsampwidth()!=2 or f.getframerate()!=24000:raise RuntimeError('Unexpected audio specs')
   out.writeframes(f.readframes(f.getnframes()))
client=OpenAI(api_key=os.environ['OPENAI_API_KEY'],timeout=100,max_retries=1)
with open('kkami_voice_joined.wav','rb') as f:
 x=client.audio.transcriptions.create(model='whisper-1',file=f,language='ko',response_format='verbose_json',timestamp_granularities=['word'],prompt='까미, 검은 강아지, 시골 장터, 꿈속에서, 천국에서 다시 만나자')
Path('kkami_kore_v2_word_times.json').write_text(json.dumps({'text':x.text,'words':[{'text':w.word,'start':w.start,'end':w.end} for w in x.words]},ensure_ascii=False,indent=2),encoding='utf8')
print('WORDS',len(x.words),flush=True)
