from pathlib import Path
import os,json,subprocess,wave
from openai import OpenAI
files=[]
for i in [1,2,3,4,5,7,8,9,10]:
 src=Path('trims')/str(i) if i<=5 else Path('batches')/str((i-1)//2)
 p=next(src.rglob(f'clip_{i:02d}.wav'))
 files.append(p)
Path('kore_list.txt').write_text('\n'.join("file '"+str(f.resolve())+"'" for f in files)+'\n')
r=subprocess.run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i','kore_list.txt','-ar','24000','-ac','1','kore_9.wav'],capture_output=True,text=True)
if r.returncode:raise RuntimeError(r.stderr)
client=OpenAI(api_key=os.environ['OPENAI_API_KEY'],timeout=110,max_retries=1)
with open('kore_9.wav','rb') as f:
 x=client.audio.transcriptions.create(model='whisper-1',file=f,language='ko',response_format='verbose_json',timestamp_granularities=['word'],prompt='까미, 검은 강아지, 시골 장터, 꿈속에서, 천국에서 다시 만나자')
out={'text':x.text,'words':[{'text':w.word,'start':w.start,'end':w.end} for w in x.words]}
Path('kkami_kore_v2_word_times.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
print('ASR_DONE',len(x.words),'words',flush=True)
