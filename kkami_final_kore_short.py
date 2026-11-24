from pathlib import Path
import json,subprocess,shutil,wave,os
from openai import OpenAI
OUT=Path('kkami_ready');OUT.mkdir(exist_ok=True)
clips=[];total=0
for i in range(1,11):
 if i<=5:
  source=Path('trim')/str(i)
  metadata=json.loads(next(source.rglob('manifest.json')).read_text(encoding='utf8'))
  text=metadata['text']
  scenes=['hook_market','adopt','childhood','years','night']
  scene=scenes[i-1]
 elif i==6:
  source=Path('dream')
  metadata=json.loads(next(source.rglob('manifest.json')).read_text(encoding='utf8'))
  text=metadata['text'];scene='dream'
 else:
  source=Path('batches')/str((i-1)//2)
  meta=json.loads(next(source.rglob('manifest.json')).read_text(encoding='utf8'))
  metadata=next(item for item in meta if item['i']==i)
  text=metadata['text'];scene=metadata['scene']
 wav=next(source.rglob(f'clip_{i:02d}.wav'))
 dst=OUT/f'clip_{i:02d}.wav';shutil.copy2(wav,dst)
 with wave.open(str(dst),'rb') as f:d=f.getnframes()/f.getframerate()
 clips.append({'i':i,'scene':scene,'text':text,'file':dst.name,'duration':round(d,3),'start':round(total,3),'end':round(total+d,3)})
 total+=d
 print('READY',i,round(d,2),'running',round(total,2),flush=True)
(OUT/'manifest.json').write_text(json.dumps({'duration':round(total,3),'clips':clips,'voice':'Kore','speed':1.25},ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'concat.txt').write_text('\n'.join("file '"+x['file']+"'" for x in clips)+'\n')
p=subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(OUT/'concat.txt'),'-ac','1','-ar','24000','-c:a','pcm_s16le',str(OUT/'full.wav')],capture_output=True,text=True)
if p.returncode:raise RuntimeError(p.stderr)
if total>179.5:raise RuntimeError('Duration exceeds 3min: '+str(total))
print('MIXED',round(total,2),flush=True)
client=OpenAI(api_key=os.environ['OPENAI_API_KEY'],timeout=100,max_retries=1)
with (OUT/'full.wav').open('rb') as f:
 a=client.audio.transcriptions.create(model='whisper-1',file=f,language='ko',response_format='verbose_json',timestamp_granularities=['word'],prompt='까미, 시골 장터, 검은 강아지, 꿈속에서 마지막 배웅, 우리 천국에서 만나자')
(OUT/'kkami_kore_v2_word_times.json').write_text(json.dumps({'text':a.text,'words':[{'text':w.word,'start':w.start,'end':w.end} for w in a.words]},ensure_ascii=False,indent=2),encoding='utf8')
print('ASR_OK',len(a.words),flush=True)
