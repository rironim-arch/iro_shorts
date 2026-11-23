import os,base64,wave,time,subprocess,json,re,difflib
from pathlib import Path
from google import genai
from faster_whisper import WhisperModel
TEXT="그 뒤 일 년 동안 아들은 아침 일찍부터 밤늦게까지 가게를 지켰습니다. 메뉴를 바꾸고 홍보도 해봤지만, 장사는 좀처럼 나아지지 않았습니다."
out=Path("cafe_mom_effort_patch");out.mkdir(exist_ok=True)
client=genai.Client(http_options={'api_version':'v1beta'},api_key=os.environ['GEMINI_API_KEY'])
asr=WhisperModel('base',device='cpu',compute_type='int8',cpu_threads=4)
def norm(x): return re.sub(r'[^0-9가-힣a-z]','',x.lower())
for n in range(5):
 try:
  reply=client.interactions.create(model='gemini-3.8-flash-tts',input=[{'type':'user_input','content':[{'type':'text','text':TEXT,'annotations':[{'type':'speech_metadata','style':'Female Korean documentary storyteller Kore voice. Natural sympathetic tone, gently convey the hardworking cafe owner struggling to save his business for a year. Same Kore as a sensitive human interest narration. Speak ALL exact Korean text with no extra words. Natural pacing, consistent volume, no music and full final syllables.'}]}]}],response_format={'type':'audio'},generation_config={'speech_config':[{'voice':'Kore'}]})
  data=reply.output_audio.data; raw=base64.b64decode(data) if isinstance(data,str) else data
  src=out/'source.wav'
  if raw[:4]==b'RIFF':src.write_bytes(raw)
  else:
   with wave.open(str(src),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000);f.writeframes(raw)
  chunks,_=asr.transcribe(str(src),language='ko',beam_size=4,condition_on_previous_text=False)
  heard=' '.join(s.text.strip() for s in chunks)
  score=difflib.SequenceMatcher(None,norm(TEXT),norm(heard),autojunk=False).ratio()
  print('ASR',round(score,3),heard,flush=True)
  if score<.75 or '가게' not in heard or '홍보' not in heard:raise RuntimeError('Read did not match script')
  q=subprocess.run(['ffmpeg','-y','-v','error','-i',str(src),'-af','loudnorm=I=-18:TP=-1.5:LRA=8,apad=pad_dur=0.18','-ar','24000','-ac','1',str(out/'effort.wav')],text=True,capture_output=True)
  if q.returncode:raise RuntimeError(q.stderr)
  with wave.open(str(out/'effort.wav')) as w:seconds=w.getnframes()/w.getframerate()
  (out/'manifest.json').write_text(json.dumps(dict(text=TEXT,heard=heard,score=round(score,3),seconds=seconds,voice='Kore',model='gemini-3.8-flash-tts'),ensure_ascii=False,indent=2))
  print('PATCH_SUCCESS',round(seconds,2),flush=True)
  break
 except Exception as e:
  print('RETRY',str(e)[:170],flush=True)
  if n==4:raise
  time.sleep(12+n*12)
