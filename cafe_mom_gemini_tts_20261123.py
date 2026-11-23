#!/usr/bin/env python3
"""Real Gemini 3.8 Korean narration for failed-cafe and mother comfort Shorts."""
from pathlib import Path
import os,time,base64,wave,re,json,difflib,subprocess
from google import genai
from faster_whisper import WhisperModel

TURNS=[["n",0,"가게를 처음 열던 날, 축하하러 온 사람은 스무 명이 넘었습니다."],["f",0,"야, 드디어 사장님 됐네! 축하한다!"],["s",0,"하하! 고맙다. 다들 자주 놀러 와!"],["n",0,"꽃다발과 웃음소리로 가득했던 작은 카페."],["n",0,"서른여덟 살 아들은 그날 세상을 다 가진 것 같았습니다."],["n",1,"하지만 장사는 생각처럼 되지 않았습니다."],["n",1,"손님은 줄어들고, 월세는 밀리기 시작했습니다."],["n",1,"결국 아들은 가게를 정리하기로 했습니다."],["n",2,"마지막 영업을 마친 날, 텅 빈 카페를 바라보며 친구에게 전화했습니다."],["s",2,"나 내일 가게 정리하는데… 혹시 시간 좀 되냐?"],["f",2,"아, 미안하다. 내일은 일이 있어서. 괜찮겠어?"],["s",2,"어, 괜찮아. 내가 하면 되지 뭐."],["n",3,"전화를 끊고 아들은 한참 동안 의자에 앉아 있었습니다."],["n",3,"다음 날, 혼자 짐을 정리하던 아들. 그때 가게 문이 열렸습니다."],["s",4,"어? 엄마? 여긴 웬일이야?"],["m",4,"오늘 가게 정리한다며."],["s",4,"그냥 나 혼자 하면 되는데…"],["n",4,"엄마는 대답 대신 가져온 장갑을 끼고 빗자루를 집어 들었습니다."],["m",5,"혼자 하면 오래 걸리잖아. 뭐부터 치우면 돼?"],["n",5,"아들은 애써 웃었습니다."],["s",5,"엄마… 나 결국 망했어."],["n",6,"엄마는 잠시 아들을 바라보더니 말했습니다."],["m",6,"가게가 안 된 거지, 네 인생이 끝난 건 아니잖아."],["n",7,"두 사람은 말없이 바닥을 쓸고 의자를 옮겼습니다."],["n",7,"한때 사람들의 웃음으로 가득했던 카페에는 이제 빗자루 소리만 들렸습니다."],["n",8,"그날 아들은 깨달았습니다."],["n",8,"내가 잘될 때 함께 웃어주는 사람도 고맙지만,"],["n",8,"모든 게 무너진 날 말없이 내 곁에서 함께 치워주는 사람이 얼마나 소중한지를."],["n",8,"그리고 그날, 아들 곁에 남아 있던 사람은 엄마였습니다."],["n",8,"이 이야기가 마음에 남으셨다면 구독과 좋아요 부탁드립니다."]]
VOICES={"n":"Kore","m":"Kore","s":"Orus","f":"Algenib"}
STYLE={
 "n":"Warm adult female Korean documentary narrator, Kore voice, natural storytelling with restrained compassionate feeling, stable gentle conversational pace. Not theatrical, avoid any introductory words. No music.",
 "m":"Loving Korean mother in her late 60s, Kore female voice, unhurried affectionate ordinary mother speaking softly to her son, not dramatic acting, no narrator intonation, calm understated assurance.",
 "s":"A Korean cafe owner aged thirty-eight, Orus male voice. At cafe opening casually happy; after shutting down weary and soft-spoken, embarrassed about failure, naturally emotional but not sobbing. Natural Korean speech.",
 "f":"Casual Korean male friend aged late thirties, Algenib voice. During opening cheerful congratulations; on call regrets he cannot help, genuine hesitant and apologetic. Natural spoken Korean without overacting."
}
OUT=Path("cafe_mom_gemini_tts")
OUT.mkdir(exist_ok=True)
client=genai.Client(http_options={"api_version":"v1beta"},api_key=os.environ["GEMINI_API_KEY"])
asr=WhisperModel("base",device="cpu",compute_type="int8",cpu_threads=4)
def cn(s):return re.sub(r'[^가-힣a-z0-9]','',s.lower())
def proc(cmd):
 p=subprocess.run(cmd,text=True,capture_output=True)
 if p.returncode:raise RuntimeError(p.stderr[-800:])
def build(i,role,scene,text):
 dest=OUT/f"line_{i:02d}.wav"
 for attempt in range(5):
  try:
   style=STYLE[role]+ " Read exactly the given Korean line, every syllable, no additions or title. No humming. Finish the last word completely before silence."
   response=client.interactions.create(
     model="gemini-3.8-flash-tts",
     input=[{"type":"user_input","content":[{"type":"text","text":text,
        "annotations":[{"type":"speech_metadata","style":style}]}]}],
     response_format={"type":"audio"},
     generation_config={"speech_config":[{"voice":VOICES[role]}]})
   voice=response.output_audio.data
   if not voice:raise RuntimeError("Empty audio output")
   blob=base64.b64decode(voice) if isinstance(voice,str) else voice
   src=OUT/f"raw_{i:02d}.wav"
   if blob[:4]==b"RIFF":src.write_bytes(blob)
   else:
    with wave.open(str(src),"wb") as f:
     f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000);f.writeframes(blob)
   with wave.open(str(src)) as w:duration=w.getnframes()/w.getframerate()
   if not (0.7<duration<35):raise RuntimeError(f"Unexpected duration {duration}")
   chunks,_=asr.transcribe(str(src),language="ko",beam_size=3,condition_on_previous_text=False)
   heard=" ".join(c.text.strip() for c in chunks)
   score=difflib.SequenceMatcher(None,cn(text),cn(heard),autojunk=False).ratio()
   if score<(.60 if len(cn(text))>14 else .51) or len(cn(heard))<.60*len(cn(text)):
    raise RuntimeError(f"ASR mismatch {score:.2f} actual={heard}")
   proc(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(src),
         "-af","loudnorm=I=-18:TP=-1.5:LRA=8,apad=pad_dur=0.18",
         "-ar","24000","-ac","1",str(dest)])
   with wave.open(str(dest)) as f:seconds=f.getnframes()/f.getframerate()
   result=dict(index=i,role=role,scene=scene,text=text,voice=VOICES[role],
      file=dest.name,seconds=round(seconds,3),asr=heard,asr_match=round(score,3),attempt=attempt+1)
   print("AUDIO_PASS",i,scene,VOICES[role],round(seconds,2),round(score,2),flush=True)
   return result
  except Exception as e:
   print("AUDIO_RETRY",i,attempt+1,str(e)[:170],flush=True)
   if attempt==4:raise
   time.sleep(13+attempt*11)
output=[]
for i,(role,scene,text) in enumerate(TURNS,1):
 output.append(build(i,role,scene,text))
 time.sleep(3)
def stamp(sec):
 ms=int(round(sec*1000));h,rem=divmod(ms,3600000);m,rem=divmod(rem,60000);s,milli=divmod(rem,1000)
 return f"{h:02d}:{m:02d}:{s:02d},{milli:03d}"
t=0.0
entries=[]
concat=[]
for i,item in enumerate(output,1):
 entries.append(f"{i}\n{stamp(t)} --> {stamp(t+item['seconds'])}\n{item['text']}\n")
 concat.append("file '"+item["file"]+"'")
 item["start"]=round(t,3)
 t+=item["seconds"]
 item["end"]=round(t,3)
(OUT/"captions.srt").write_text("\n".join(entries),encoding="utf-8")
(OUT/"concat.txt").write_text("\n".join(concat)+"\n",encoding="utf8")
proc(["ffmpeg","-hide_banner","-y","-loglevel","error","-f","concat","-safe","0","-i",str(OUT/"concat.txt"),"-c:a","pcm_s16le",str(OUT/"full.wav")])
proc(["ffmpeg","-hide_banner","-y","-loglevel","error","-i",str(OUT/"full.wav"),"-c:a","libmp3lame","-b:a","128k",str(OUT/"full.mp3")])
(OUT/"manifest.json").write_text(json.dumps({"title":"가게가 망한 날 마지막으로 찾아온 사람",
 "voices":VOICES,"model":"gemini-3.8-flash-tts","turns":output,"seconds":round(t,3)},ensure_ascii=False,indent=2),encoding="utf8")
print("ALL_AUDIO_COMPLETE",len(output),round(t,2),flush=True)
