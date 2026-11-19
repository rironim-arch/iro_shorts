#!/usr/bin/env python3
import json, os, zipfile, glob
from faster_whisper import WhisperModel
import subprocess
from pathlib import Path
zipfile.ZipFile('/tmp/baekgu_original.zip').extractall('/tmp/baekgu_original')
p=Path('/tmp/baekgu_original')
data=json.loads((p/'timing.json').read_text())
model=WhisperModel('small',device='cpu',compute_type='int8')
res=[]
for i,expected in enumerate(data['scenes']):
    f=p/f'segment_{i:02d}.wav'
    segs,_=model.transcribe(str(f),language='ko',beam_size=5,condition_on_previous_text=False,vad_filter=False,word_timestamps=True)
    found=[]
    for s in segs:
        found.append({'start':round(s.start,2),'end':round(s.end,2),'text':s.text,'words':[{'start':round(w.start,2),'end':round(w.end,2),'word':w.word} for w in s.words or []]})
    item={'i':i,'expected':expected['text'],'transcription':found,'duration':expected['duration']}
    res.append(item)
    print('SENTENCE',i,'EXPECTED',expected['text'],flush=True)
    print('TRANSCRIBED',' / '.join(x['text'] for x in found),flush=True)
Path('baekgu_asr_full.json').write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf8')
