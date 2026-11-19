import json, pathlib, subprocess
from faster_whisper import WhisperModel
p=pathlib.Path('/tmp/father_dawn_kore_audio')
p.mkdir(parents=True,exist_ok=True)
subprocess.run(['unzip','-q','/tmp/father_dawn_voice.zip','-d',str(p)],check=True)
data=json.loads((p/'timing.json').read_text(encoding='utf8'))
model=WhisperModel('small',device='cpu',compute_type='int8')
results=[]
for s in data['scenes']:
 i=s['i']
 f=p/f'segment_{i:02d}.wav'
 segs,meta=model.transcribe(str(f),language='ko',beam_size=5,condition_on_previous_text=False,vad_filter=False)
 items=[{'start':round(x.start,2),'end':round(x.end,2),'text':x.text} for x in segs]
 info={'i':i,'expected':s['text'],'recognized':items,'duration':s['duration']}
 results.append(info)
 print('SCENE',i,'EXPECT',s['text'],flush=True)
 print('RECOGNIZED',' | '.join(x['text'] for x in items),flush=True)
pathlib.Path('father_dawn_voice_qa.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
