import os, time, json, base64, wave, traceback
from pathlib import Path
from google import genai
from google.genai import types
out=Path('kkami_kore_probe');out.mkdir(exist_ok=True)
client=genai.Client(api_key=os.environ['GEMINI_API_KEY'],http_options=types.HttpOptions(api_version='v1beta',timeout=30000))
line='어릴 적, 시골 장터에서 만난 작고 검은 강아지. 나는 그 아이에게 까미라는 이름을 지어주었습니다.'
print('START Gemini',flush=True)
try:
 resp=client.interactions.create(model='gemini-3.8-flash-tts',input=[{'type':'user_input','content':[{'type':'text','text':line,'annotations':[{'type':'speech_metadata','style':'Kore warm Korean female narrator, natural emotional storytelling, gentle nostalgic pace, no exaggerated sorrow. Read only the Korean script and finish all syllables clearly.'}]}]}],response_format={'type':'audio'},generation_config={'speech_config':[{'voice':'Kore'}]})
 data=resp.output_audio.data
 raw=base64.b64decode(data) if isinstance(data,str) else data
 file=out/'probe.wav'
 if raw[:4]==b'RIFF':file.write_bytes(raw)
 else:
  with wave.open(str(file),'wb') as f:
   f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000);f.writeframes(raw)
 print('SUCCESS',file.stat().st_size,flush=True)
except Exception as ex:
 print('FAIL',type(ex).__name__,str(ex)[:1200],flush=True)
 raise
