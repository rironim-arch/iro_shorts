from pathlib import Path
import os,time,json,wave,base64,subprocess
from google import genai
out=Path('dad_diary_quick');out.mkdir(exist_ok=True)
lines={2:"그런데 어느 날, 초등학생 딸의 일기장을 읽다가 끝내 눈물을 흘렸습니다.",16:"어느 날, 딸의 책상 위에 놓인 일기장이 눈에 들어왔습니다.",37:"성호는 딸의 일기장을 덮고 조용히 딸을 안아주었습니다.",38:"그제야 그는 알았습니다. 인생의 내리막길에서도, 함께하는 저녁처럼 소중한 행복은 사라지지 않는다는 것을."}
client=genai.Client(http_options={"api_version":"v1beta"},api_key=os.environ["GEMINI_API_KEY"])
outputs=[]
for key,txt in lines.items():
 for attempt in range(4):
  try:
   response=client.interactions.create(model="gemini-3.8-flash-tts",input=[{"type":"user_input","content":[{"type":"text","text":txt,"annotations":[{"type":"speech_metadata","style":"Voice Kore. Female Korean narrator naturally speaking heartfelt family story at steady clear volume. Not theatrical, no music. Read exact entire Korean line, no additions, clean final syllables."}]}]}],response_format={"type":"audio"},generation_config={"speech_config":[{"voice":"Kore"}]})
   audio=response.output_audio.data
   data=base64.b64decode(audio) if isinstance(audio,str) else audio
   s=out/f'raw_{key:02d}.wav';p=out/f'clip_{key:02d}.wav'
   if data[:4]==b'RIFF':s.write_bytes(data)
   else:
    with wave.open(str(s),'wb') as f:
     f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000);f.writeframes(data)
   proc=subprocess.run(['ffmpeg','-v','error','-y','-i',str(s),'-af','loudnorm=I=-18:TP=-1.5:LRA=10,atempo=1.25,apad=pad_dur=0.12','-ar','24000','-ac','1',str(p)],capture_output=True,text=True)
   if proc.returncode:raise RuntimeError(proc.stderr)
   with wave.open(str(p),'rb') as f:dur=f.getnframes()/f.getframerate()
   outputs.append({'i':key,'text':txt,'duration':dur,'file':p.name,'words':[]})
   print('FINISHED_LINE',key,dur,flush=True)
   break
  except Exception as e:
   print('RETRY',key,str(e)[:150],flush=True)
   if attempt==3:raise
   time.sleep(14)
(out/'manifest.json').write_text(json.dumps(outputs,ensure_ascii=False,indent=2),encoding='utf8')
