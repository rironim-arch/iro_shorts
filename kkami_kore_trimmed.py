from pathlib import Path
import os,base64,wave,time,subprocess,json
from google import genai
TEXTS={
1:"까미는 마지막 순간에도 나를 지켜주었습니다. 꿈속에서까지요. 어린 시절 시골 장터, 낡은 상자 안에는 강아지 다섯 마리가 있었습니다.",
2:"다른 강아지들은 장난쳤지만, 작고 까만 한 아이만 구석에서 떨고 있었죠. 엄마, 나 저 아이 데려갈래. 그날 나는 까미를 품에 안고 집에 돌아왔습니다.",
3:"내가 지켜주려던 까미는 어느새 나를 지켜주고 있었습니다. 속상해서 울던 날엔 곁에 앉아주었고, 무서운 시골길에선 항상 내 앞에서 걸어줬죠.",
4:"늦게 귀가하면 대문 앞에서 기다리던 까미. 그렇게 나는 어른이 되었고, 까미 얼굴에는 흰 털이 늘었습니다. 열다섯 해가 지나자 혼자 일어나기도 힘들어했어요.",
5:"마지막 밤, 나는 까미 옆에 누웠습니다. 까미야, 많이 힘들지? 오늘은 내가 옆에 있을게. 등을 쓰다듬다 잠든 나는 이상한 꿈을 꾸었습니다."
}
i=int(os.environ['INDEX']);txt=TEXTS[i];dest=Path('kkami_trim');dest.mkdir(exist_ok=True)
client=genai.Client(http_options={'api_version':'v1beta','timeout':65000},api_key=os.environ['GEMINI_API_KEY'])
for attempt in range(2):
 try:
  print('GENERATE_TRIMMED',i,attempt,flush=True)
  r=client.interactions.create(model='gemini-3.8-flash-tts',input=[{'type':'user_input','content':[{'type':'text','text':txt,'annotations':[{'type':'speech_metadata','style':'Female Kore Korean emotional drama narrator. Warm nostalgic beginning, natural real woman voice, steady volume, tender realistic sadness. Korean clear complete syllables, no extra words, no background sound.'}]}]}],response_format={'type':'audio'},generation_config={'speech_config':[{'voice':'Kore'}]})
  a=r.output_audio.data;data=base64.b64decode(a) if isinstance(a,str) else a
  src=dest/'raw.wav';out=dest/f'clip_{i:02d}.wav'
  if data[:4]==b'RIFF':src.write_bytes(data)
  else:
   with wave.open(str(src),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(data)
  p=subprocess.run(['ffmpeg','-v','error','-y','-i',str(src),'-af','loudnorm=I=-18:TP=-1.5:LRA=9,atempo=1.25,apad=pad_dur=0.1','-ar','24000','-ac','1',str(out)],capture_output=True,text=True,timeout=40)
  if p.returncode:raise RuntimeError(p.stderr)
  with wave.open(str(out),'rb') as w:d=w.getnframes()/w.getframerate()
  (dest/'manifest.json').write_text(json.dumps({'i':i,'text':txt,'duration':round(d,3),'file':out.name},ensure_ascii=False,indent=2),encoding='utf8')
  print('TRIM_SUCCESS',i,round(d,2),flush=True)
  break
 except Exception as e:
  print('TRIM_FAIL',i,attempt,type(e).__name__,str(e)[:250],flush=True)
  if attempt==1:raise
  time.sleep(3)
