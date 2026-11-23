from pathlib import Path
import os, time,base64,wave,re,json,difflib,subprocess
from google import genai
from faster_whisper import WhisperModel
text="성호는 딸을 꼭 안아주었습니다."
out=Path("father_daughter_retakes");out.mkdir(exist_ok=True)
client=genai.Client(http_options={"api_version":"v1beta"},api_key=os.environ['GEMINI_API_KEY'])
asr=WhisperModel('small',device='cpu',compute_type='int8',cpu_threads=4)
def normalize(t):return re.sub('[^가-힣a-z0-9]','',t.lower())
for attempt in range(6):
 try:
  response=client.interactions.create(model='gemini-3.8-flash-tts',input=[{'type':'user_input','content':[{'type':'text','text':text,'annotations':[{'type':'speech_metadata','style':"Voice Kore. A tender, mature Korean woman who narrates emotional family stories. Speak clearly: '성호는' (Seong-ho-neun) and '딸을' (ttal-eul). Calm soft storytelling natural speed, speak exact supplied Korean text in full only, without extras. Complete the ending clearly."}]}]}],response_format={'type':'audio'},generation_config={'speech_config':[{'voice':'Kore'}]})
  d=response.output_audio.data; b=base64.b64decode(d) if isinstance(d,str) else d
  src=out/'raw.wav'
  if b[:4]==b'RIFF':src.write_bytes(b)
  else:
   with wave.open(str(src),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(b)
  p=subprocess.run(['ffmpeg','-y','-hide_banner','-v','error','-i',str(src),'-af','loudnorm=I=-18:TP=-1.5:LRA=10,atempo=1.25,apad=pad_dur=0.12','-ar','24000','-ac','1',str(out/'retake31.wav')],capture_output=True,text=True)
  if p.returncode:raise RuntimeError(p.stderr)
  segments,_=asr.transcribe(str(out/'retake31.wav'),language='ko',beam_size=5,condition_on_previous_text=False,word_timestamps=True)
  ww=[];heard=[]
  for s in segments:
   for w in s.words or []:ww.append({'text':w.word,'start':w.start,'end':w.end});heard.append(w.word)
  sentence=' '.join(heard)
  score=difflib.SequenceMatcher(None,normalize(text),normalize(sentence),autojunk=False).ratio()
  print('attempt',attempt,'score',score,'heard',sentence,flush=True)
  if score<.90 or '딸' not in sentence or '성호' not in sentence:raise RuntimeError('Insufficient pronunciation certainty')
  with wave.open(str(out/'retake31.wav')) as wav:seconds=wav.getnframes()/wav.getframerate()
  (out/'retake31.json').write_text(json.dumps({'text':text,'heard':sentence,'match':score,'duration':seconds,'words':ww},ensure_ascii=False,indent=2))
  break
 except Exception as e:
  print('retry',attempt+1,str(e)[:120],flush=True)
  if attempt==5:raise
  time.sleep(9)
