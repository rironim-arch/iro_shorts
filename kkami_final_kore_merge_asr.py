from pathlib import Path
import json,subprocess,shutil,wave,os
from openai import OpenAI
OUT=Path('kkami_final_audio');OUT.mkdir(exist_ok=True)
records=[];t=0
for i in range(1,11):
 base=Path('batches')/str((i-1)//2)
 if i<=5:
  trim=Path('trims')/str(i)
  wav=next(trim.rglob(f'clip_{i:02d}.wav'))
  meta=json.loads(next(trim.rglob('manifest.json')).read_text(encoding='utf8'))
  scene=json.loads(next(base.rglob('manifest.json')).read_text(encoding='utf8'))[0 if i%2==1 else 1]['scene']
  text=meta['text']
 else:
  wav=next(base.rglob(f'clip_{i:02d}.wav'))
  b=json.loads(next(base.rglob('manifest.json')).read_text(encoding='utf8'))
  meta=next(x for x in b if x['i']==i)
  scene=meta['scene'];text=meta['text']
 dst=OUT/f'clip_{i:02d}.wav';shutil.copy2(wav,dst)
 with wave.open(str(dst),'rb') as w:d=w.getnframes()/w.getframerate()
 records.append(dict(i=i,scene=scene,text=text,file=dst.name,duration=round(d,3),start=round(t,3),end=round(t+d,3)))
 t+=d
 print("MERGE",i,round(d,2),"total",round(t,2),flush=True)
(OUT/'manifest.json').write_text(json.dumps({'duration':round(t,3),'clips':records,'voice':'Kore','speed':1.25},ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'concat.txt').write_text('\n'.join("file '"+r['file']+"'" for r in records)+'\n')
p=subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(OUT/'concat.txt'),'-ac','1','-ar','24000','-c:a','pcm_s16le',str(OUT/'full.wav')],capture_output=True,text=True)
if p.returncode:raise RuntimeError(p.stderr)
if t>=179.8:raise RuntimeError(f"Length exceeds user strict 3min requirement: {t}")
client=OpenAI(api_key=os.environ['OPENAI_API_KEY'],timeout=110,max_retries=1)
with (OUT/'full.wav').open('rb') as f:
 a=client.audio.transcriptions.create(model="whisper-1",file=f,language='ko',response_format='verbose_json',timestamp_granularities=['word'],prompt='까미, 검은 강아지, 시골 장터, 꿈속 배웅, 우리 천국에서 꼭 다시 만나자')
(OUT/'kkami_kore_v2_word_times.json').write_text(json.dumps({'text':a.text,'words':[{'text':w.word,'start':w.start,'end':w.end} for w in a.words]},ensure_ascii=False,indent=2),encoding='utf8')
print('FINAL_SUCCESS',round(t,2),'seconds',len(a.words),'words',flush=True)
