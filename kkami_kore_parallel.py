from pathlib import Path
import os,sys,time,base64,wave,json,re,subprocess
from google import genai
src=Path('kkami_kore_v2.py').read_text(encoding='utf8')
groups=json.loads(re.search(r'^GROUPS=(.*)$',src,re.M).group(1))
batch=int(os.environ["BATCH"])
indexes=list(range(batch*2,min(batch*2+2,len(groups))))
out=Path(f'kkami_parallel_{batch}');out.mkdir(exist_ok=True)
client=genai.Client(http_options={"api_version":"v1beta","timeout":65000},api_key=os.environ["GEMINI_API_KEY"])
records=[]
for j in indexes:
 item=groups[j];i=j+1;line=item['text']
 for attempt in range(2):
  try:
   print('START',i,'attempt',attempt+1,flush=True)
   response=client.interactions.create(model='gemini-3.8-flash-tts',input=[{'type':'user_input','content':[{'type':'text','text':line,'annotations':[{'type':'speech_metadata','style':'Kore natural Korean woman narrating a loving black dog memory. Genuine heartfelt emotion, warm childhood, soft awe in dream, restrained sorrow only at end. Not announcer style. No extra words or sounds; every syllable fully spoken.'}]}]}],response_format={'type':'audio'},generation_config={'speech_config':[{'voice':'Kore'}]})
   audio=response.output_audio.data
   if not audio:raise RuntimeError('empty TTS result')
   raw=base64.b64decode(audio) if isinstance(audio,str) else audio
   source=out/f'raw_{i:02}.wav';target=out/f'clip_{i:02}.wav'
   if raw[:4]==b'RIFF':source.write_bytes(raw)
   else:
    with wave.open(str(source),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000);f.writeframes(raw)
   p=subprocess.run(['ffmpeg','-y','-v','error','-i',str(source),'-af','loudnorm=I=-18:TP=-1.5:LRA=9,atempo=1.25,apad=pad_dur=0.1','-ar','24000','-ac','1',str(target)],capture_output=True,text=True,timeout=30)
   if p.returncode:raise RuntimeError(p.stderr)
   with wave.open(str(target),'rb') as f:duration=f.getnframes()/f.getframerate()
   if not 3<duration<75:raise RuntimeError('invalid duration')
   records.append(dict(i=i,scene=item['scene'],text=line,file=target.name,duration=round(duration,3)))
   print('SUCCESS',i,duration,flush=True)
   (out/'manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf8')
   break
  except Exception as e:
   print('FAIL',i,attempt,type(e).__name__,str(e)[:200],flush=True)
   if attempt==1:raise
   time.sleep(4)
