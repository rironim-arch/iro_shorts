from pathlib import Path
import os,base64,wave,json,time,subprocess
from google import genai
text="꿈속에서 익숙한 발소리가 들렸습니다. 돌아보니 까미가 젊고 건강한 모습으로 꼬리를 흔들고 있었습니다."
out=Path('kkami_group6short');out.mkdir(exist_ok=True)
client=genai.Client(http_options={'api_version':'v1beta','timeout':60000},api_key=os.environ["GEMINI_API_KEY"])
for attempt in range(2):
 try:
  print('START_GROUP6',attempt+1,flush=True)
  r=client.interactions.create(model='gemini-3.8-flash-tts',input=[{'type':'user_input','content':[{'type':'text','text':text,'annotations':[{'type':'speech_metadata','style':'Female Kore Korean narration, dreamlike wonder, nostalgic warmth, clear authentic natural dialogue, no music or sound effects, speak entire Korean text only and finish all syllables.'}]}]}],response_format={'type':'audio'},generation_config={'speech_config':[{'voice':'Kore'}]})
  a=r.output_audio.data;raw=base64.b64decode(a) if isinstance(a,str) else a
  src=out/'source.wav';dst=out/'clip_06.wav'
  if raw[:4]==b'RIFF':src.write_bytes(raw)
  else:
   with wave.open(str(src),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000);f.writeframes(raw)
  p=subprocess.run(['ffmpeg','-y','-v','error','-i',str(src),'-af','loudnorm=I=-18:TP=-1.5:LRA=9,atempo=1.25,apad=pad_dur=0.1','-ar','24000','-ac','1',str(dst)],capture_output=True,text=True,timeout=35)
  if p.returncode:raise RuntimeError(p.stderr)
  with wave.open(str(dst),'rb') as f:d=f.getnframes()/f.getframerate()
  (out/'manifest.json').write_text(json.dumps({'i':6,'scene':'dream','text':text,'duration':round(d,3),'file':'clip_06.wav'},ensure_ascii=False,indent=2),encoding='utf8')
  print('GROUP6_DONE',round(d,2),flush=True)
  break
 except Exception as e:
  print('FAIL',attempt,type(e).__name__,str(e)[:200],flush=True)
  if attempt:raise
  time.sleep(4)
