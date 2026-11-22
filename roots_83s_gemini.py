#!/usr/bin/env python3
"""Emotional father-and-son 'invisible roots' vertical video Gemini line TTS.
Each line is a fully separate generated and untrimmed WAV, with trailing silence to protect endings.
"""
import os, re, json, time, wave, subprocess, difflib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from google.genai import types
TURNS=[{"r":"son","s":0,"t":"아버지… 저는 실패한 인생인가 봐요."},{"r":"narrator","s":0,"t":"마흔을 앞둔 아들은 동창 모임에서 돌아와 한숨을 쉬었습니다."},{"r":"narrator","s":1,"t":"친구들은 승진하고 집을 샀지만, 아들은 2년째 재취업을 준비하고 있었죠."},{"r":"son","s":2,"t":"다들 앞으로 가는데… 저만 제자리예요."},{"r":"narrator","s":3,"t":"그 말을 들은 아버지는 아무 말 없이 삽을 들고 마당으로 나갔습니다."},{"r":"son","s":3,"t":"아버지, 갑자기 뭐 하세요?"},{"r":"narrator","s":4,"t":"아버지는 3년 전, 아들이 직접 심은 작은 나무를 가리켰습니다."},{"r":"father","s":4,"t":"저 나무, 처음 심었을 때 기억나냐?"},{"r":"son","s":4,"t":"네. 그런데 아직도 이렇게 작네요."},{"r":"father","s":4,"t":"겉으로는 안 자란 것 같지?"},{"r":"narrator","s":5,"t":"아버지는 나무 옆의 흙을 조심스럽게 걷어냈습니다."},{"r":"narrator","s":6,"t":"그러자 땅속 깊이 뻗어 있는 뿌리가 드러났습니다."},{"r":"father","s":6,"t":"보렴. 보이지 않는 동안에도 뿌리는 자라고 있었단다."},{"r":"son","s":6,"t":"그런데… 그게 제 인생이랑 무슨 상관이에요?"},{"r":"father","s":7,"t":"너도 지난 2년 동안 아무것도 안 한 게 아니잖니."},{"r":"father","s":7,"t":"떨어져도 다시 면접을 봤고, 새로운 공부도 시작했지."},{"r":"father","s":7,"t":"힘든 와중에도 아픈 엄마 병원에 꼬박꼬박 모시고 갔고."},{"r":"narrator","s":7,"t":"아들은 아무 대답도 하지 못했습니다."},{"r":"father","s":7,"t":"남들은 네가 얼마나 높이 올라갔는지만 보겠지."},{"r":"father","s":7,"t":"하지만 아버지는 안다."},{"r":"father","s":7,"t":"네가 무너지지 않으려고 얼마나 애썼는지."},{"r":"narrator","s":8,"t":"그날 밤, 아들은 포기하려던 이력서를 다시 펼쳤습니다."},{"r":"narrator","s":8,"t":"지금까지의 시간이 모두 헛된 것은 아니라는 걸, 이제는 알 것 같았습니다."},{"r":"narrator","s":8,"t":"누군가에겐 멈춰 있는 시간도, 다시 일어설 힘을 기르는 시간일 수 있습니다."},{"r":"cta","s":8,"t":"이 이야기가 마음에 남으셨다면 구독과 좋아요 부탁드립니다."}]
OUT=Path("roots_tts_audio");OUT.mkdir(exist_ok=True)
assert len(TURNS)==25 and sum("구독과 좋아요" in x["t"] for x in TURNS)==1
VOICE={"son":"Orus","narrator":"Kore","father":"Enceladus","cta":"Kore"}
STYLE={
"son":"A natural Korean man around age 39 who is exhausted, discouraged, but restrained. In the opening line, briefly emotional but still fully intelligible; a slightly rough conversational male voice. In the later questions, curious and vulnerable. Speak naturally and consistently.",
"narrator":"A Korean adult female documentary storyteller, Kore. Warm professional voice with strong meaningful pacing, emphasis on key images and emotion, neither rushed nor excessively dramatic.",
"father":"A wise Korean elderly father around 73, male voice Enceladus. Calm, loving, low-register, slightly aged timbre and warm. Speak naturally with empathy. Be emotional on '하지만 아버지는 안다' and the next line, with all final syllables fully spoken.",
"cta":"The same adult Korean female narrator speaking in a sincere and calm closing voice, no overly promotional excitement."
}
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
def cmd(*args):
 p=subprocess.run([str(x) for x in args],capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stderr[-600:])
def generate(i,t):
 role=t["r"];text=t["t"];voice=VOICE[role]
 prompt=(STYLE[role]+" Speak in natural native Korean. Read ONLY the script written below. "
 "Say every word including the complete very last syllable. Do not truncate, paraphrase, repeat, add instructions or roles, sing, "
 "change speed wildly, or leave long silences. Leave a brief silence after completion. "
 "짧은 한 문장의 대사를 끝까지 정확하게 읽어 주세요. 문장 시작과 끝을 자르지 마세요.\nSCRIPT:\n"+text)
 raw=OUT/f"raw_{i:02d}.wav"; output=OUT/f"turn_{i:02d}.wav"
 for k in range(5):
  try:
   resp=client.models.generate_content(model="gemini-2.5-flash-preview-tts",contents=prompt,config=types.GenerateContentConfig(
    response_modalities=["AUDIO"],speech_config=types.SpeechConfig(
      voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)))))
   inline=next(p.inline_data for cand in resp.candidates for p in cand.content.parts
      if getattr(p,"inline_data",None) and getattr(p.inline_data,"data",None))
   if inline.data[:4]==b"RIFF":raw.write_bytes(inline.data)
   else:
    mtch=re.search(r"rate=(\d+)",inline.mime_type or "")
    with wave.open(str(raw),"wb") as w:
     w.setnchannels(1);w.setsampwidth(2);w.setframerate(int(mtch.group(1)) if mtch else 24000);w.writeframes(inline.data)
   with wave.open(str(raw),"rb") as w:seconds=w.getnframes()/w.getframerate()
   if not 0.8 < seconds < 19: raise ValueError(f"unexpected duration {seconds}")
   # Normalize per line without shortening words; 220ms silent tail to guard end words.
   cmd("ffmpeg","-y","-v","error","-i",str(raw),"-af",
       "loudnorm=I=-18:TP=-2:LRA=8,apad=pad_dur=0.22","-ar","24000","-ac","1",str(output))
   with wave.open(str(output),"rb") as w:duration=w.getnframes()/w.getframerate()
   print(f"TTS_OK {i:02d} {voice} {duration:.3f} {text}",flush=True)
   return {"index":i,**t,"voice":voice,"file":output.name,"seconds":round(duration,4),"attempts":k+1}
  except Exception as e:
   print("RETRY",i,k,str(e)[:200],flush=True)
   if k==4:raise
   time.sleep(5+10*k)
out=[None]*len(TURNS)
with ThreadPoolExecutor(max_workers=3) as ex:
 futures={ex.submit(generate,i,t):i for i,t in enumerate(TURNS)}
 for f in as_completed(futures):
  i=futures[f];out[i]=f.result()
print("START ASR",flush=True)
try:
 from faster_whisper import WhisperModel
 m=WhisperModel("base",device="cpu",compute_type="int8",cpu_threads=4)
 for t in out:
  spans,_=m.transcribe(str(OUT/t["file"]),language="ko",beam_size=3,condition_on_previous_text=False,vad_filter=False)
  heard=" ".join(c.text.strip() for c in spans).strip()
  clean=lambda s:re.sub(r"[^0-9a-z가-힣]","",s.lower())
  score=difflib.SequenceMatcher(None,clean(t["t"]),clean(heard),autojunk=False).ratio()
  t["asr"]=heard;t["asr_similarity"]=round(score,3)
  print(f"ASR_QA {t['index']:02d} {score:.3f} [{heard}]",flush=True)
  if score < 0.2:print(f"ASR_ALERT low similarity {t['index']}",flush=True)
except Exception as e:
 print("ASR_NOT_AVAILABLE",str(e)[:150],flush=True)
manifest={"title":"실패한 아들 앞에서 아버지가 땅을 판 이유",
 "description":"실사풍 감동사연. 뿌리는 눈에 보이지 않는 시간에도 자랍니다.",
 "voice_provider":"Gemini 2.5 Flash TTS","voice_map":VOICE,
 "turns":out,"raw_duration":round(sum(t["seconds"] for t in out),3),"target_speed":1.25}
(OUT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf8")
print("PACKAGE_OK",len(out),manifest["raw_duration"],flush=True)
