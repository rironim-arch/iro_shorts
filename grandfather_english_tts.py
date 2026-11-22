#!/usr/bin/env python3
"""Gemini Kore/Orus line-by-line 73yo grandfather English study story.
No line splicing: each entire line is synthesized, ASR checked, and padded after final phoneme.
"""
import json,re,os,time,wave,subprocess,threading,math
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from google import genai
from google.genai import types
from faster_whisper import WhisperModel
import numpy as np
TURNS=[{"role":"son","text":"아버지, 일흔셋에 영어를 배워서 어디에 쓰시려고요?","scene":0},{"role":"father","text":"꼭 해보고 싶은 게 있어서 그런다.","scene":0},{"role":"narrator","text":"일흔셋 아버지가 갑자기 영어 공부를 시작했습니다.","scene":1},{"role":"narrator","text":"평생 공장에서 일하신 아버지는 영어로 자기소개조차 못 하셨습니다.","scene":1},{"role":"narrator","text":"그런데 매일 밤 같은 문장을 반복하고 또 반복하셨죠.","scene":1},{"role":"son","text":"아버지, 요즘 번역기도 잘 나오는데 왜 그렇게 고생하세요?","scene":2},{"role":"father","text":"기계가 대신해 줄 수 없는 것도 있단다.","scene":2},{"role":"narrator","text":"사실 아버지에게는 미국인 남편과 결혼해 미국에서 살고 있는 딸이 있었습니다.","scene":4},{"role":"narrator","text":"그리고 미국에서 태어난 일곱 살 손녀가 있었죠.","scene":4},{"role":"narrator","text":"매주 영상통화를 할 때 손녀는 신나게 이야기했지만, 아버지는 알아듣지 못해 그저 웃기만 했습니다.","scene":3},{"role":"girl","text":"Grandpa! Guess what happened today!","scene":3,"lang":"en"},{"role":"narrator","text":"그러던 어느 날 손녀가 엄마에게 물었습니다.","scene":4},{"role":"girl","text":"Mom, why does Grandpa only smile?","scene":4,"lang":"en"},{"role":"narrator","text":"엄마, 할아버지는 왜 웃기만 해? 딸에게 그 말을 전해 들은 아버지는 한참 말이 없었습니다.","scene":5},{"role":"narrator","text":"그리고 그날부터 매일 하루 한 문장씩 영어를 외우셨습니다.","scene":6},{"role":"narrator","text":"틀리면 다시 읽고, 잊으면 수첩에 적었습니다.","scene":6},{"role":"narrator","text":"그렇게 여섯 달이 흘렀습니다.","scene":6},{"role":"narrator","text":"딸 가족이 한국에 온 날, 공항에서 손녀를 만난 아버지는 떨리는 목소리로 말했습니다.","scene":7},{"role":"father","text":"Hello, sweetheart. I've missed you so much.","scene":7,"lang":"en"},{"role":"girl","text":"Grandpa! You can speak English!","scene":7,"lang":"en"},{"role":"father","text":"A little. Tell me about your day.","scene":7,"lang":"en"},{"role":"narrator","text":"손녀는 환하게 웃으며 할아버지 손을 잡고 통역 없이 이야기를 시작했습니다.","scene":8},{"role":"narrator","text":"모든 말을 알아듣지는 못했지만, 아버지는 다시 물으며 끝까지 귀를 기울였습니다.","scene":8},{"role":"son","text":"아버지… 손녀 때문에 영어를 배우신 거예요?","scene":8},{"role":"father","text":"내가 영어를 잘하려는 게 아니다.","scene":8},{"role":"father","text":"우리 손녀가 하고 싶은 말을… 내 귀로 직접 듣고 싶었을 뿐이다.","scene":8},{"role":"narrator","text":"배움에는 정해진 나이가 없습니다. 일흔셋에도 누군가의 마음에 한 걸음 더 가까워질 수 있으니까요.","scene":8},{"role":"cta","text":"이 이야기가 마음에 남으셨다면 구독과 좋아요 부탁드립니다.","scene":8}]
OUT=Path("grandfather_english_audio"); OUT.mkdir(exist_ok=True)
assert len(TURNS)==28
assert sum("구독과 좋아요" in t["text"] for t in TURNS)==1
VOICE={"son":"Orus","father":"Orus","narrator":"Kore","girl":"Kore","cta":"Kore"}
STYLE={
 "son":"You are the 40-year-old Korean son, clear energetic male Korean actor, gently skeptical then moved; conversational, never exaggerated.",
 "father":"You are a 73-year-old Korean grandfather, mature and low, naturally slow thoughtful, slightly husky but legible. On English lines sound an elderly Korean learner: understandable, with a little Korean accent and sincere emotion, never an American fluent announcer.",
 "narrator":"You are a professional calm emotional adult Korean female storyteller; gentle, compelling, 3rd-person, balanced pace and constant volume, no theatrical shouting.",
 "girl":"You are the loving seven-year-old granddaughter raised in the United States. Bright excited English with a youthful bubbly voice, not a robotic adult reading a script.",
 "cta":"You are the same warm Korean female narrator voice as Kore, relaxed, one complete clear closing sentence, not fast."
}
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
def shell(*args):
 p=subprocess.run([str(a) for a in args],capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stderr[-500:])
def produce(i,t):
 role=t["role"];voice=VOICE[role];line=t["text"]
 is_en=t.get("lang")=="en"
 prompt=(
  STYLE[role]+
  (" Read exactly the ONE English sentence shown below in English, without Korean translation or any other speech." if is_en else
   " 다음 한국어 대사 딱 한 개만 완전하게 읽으세요. 대사 앞뒤로 설명, 번호, 역할 이름, 군더더기 말을 넣지 마세요.")+
  " Deliver ALL words and the COMPLETE FINAL syllable. Do not stop early. "
  "Do not repeat, sing, insert background sounds, or pause excessively. "
  "Leave a tiny silence after finishing.\n\nSCRIPT:\n"+line)
 raw=OUT/f"raw_{i:02d}.wav";final=OUT/f"turn_{i:02d}.wav"
 for tries in range(5):
  try:
   resp=client.models.generate_content(model="gemini-2.5-flash-preview-tts",contents=prompt,
    config=types.GenerateContentConfig(response_modalities=["AUDIO"],
     speech_config=types.SpeechConfig(
      voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)))))
   pkt=next(x.inline_data for c in resp.candidates for x in c.content.parts
            if getattr(x,"inline_data",None) and getattr(x.inline_data,"data",None))
   if pkt.data[:4]==b"RIFF":raw.write_bytes(pkt.data)
   else:
    m=re.search(r"rate=(\d+)",pkt.mime_type or "")
    with wave.open(str(raw),"wb") as w:
     w.setnchannels(1);w.setsampwidth(2);w.setframerate(int(m.group(1)) if m else 24000);w.writeframes(pkt.data)
   with wave.open(str(raw),"rb") as w:secs=w.getnframes()/w.getframerate()
   if secs<1.1 or secs>19:raise RuntimeError(f"Unexpected length {secs:.2f}s")
   # Preserve the entire generated recording; add 260 ms trailing silence to avoid chopped endings.
   shell("ffmpeg","-y","-hide_banner","-v","error","-i",raw,
      "-af","loudnorm=I=-18:TP=-2:LRA=8,apad=pad_dur=0.26","-ar","24000","-ac","1",final)
   with wave.open(str(final),"rb") as w:duration=w.getnframes()/w.getframerate()
   print(f"TTS_DONE {i:02d} {role} {voice} {duration:.2f} {line}",flush=True)
   return {"index":i,**t,"voice":voice,"file":final.name,"seconds":round(duration,4),"takes":tries+1}
  except Exception as e:
   print("TTS_RETRY",i,tries,str(e)[:180],flush=True)
   if tries==4:raise
   time.sleep(3+tries*7)
out=[None]*len(TURNS)
with ThreadPoolExecutor(max_workers=3) as ex:
 futures={ex.submit(produce,i,t):i for i,t in enumerate(TURNS)}
 for f in as_completed(futures):
  i=futures[f];out[i]=f.result()
print("START_ASR_QA",flush=True)
asr=WhisperModel("base",device="cpu",compute_type="int8",cpu_threads=4)
for t in out:
  chunks,_=asr.transcribe(str(OUT/t["file"]),language="en" if t.get("lang")=="en" else "ko",
                          beam_size=3,condition_on_previous_text=False,vad_filter=False)
  txt=" ".join(c.text.strip() for c in chunks)
  t["asr"]=txt
  e=re.sub(r"[^a-z0-9가-힣]","",t["text"].lower())
  o=re.sub(r"[^a-z0-9가-힣]","",txt.lower())
  import difflib
  score=difflib.SequenceMatcher(None,e,o,autojunk=False).ratio()
  t["asr_match"]=round(score,3)
  last=(re.sub(r"[^a-z0-9가-힣]","",t["text"].split()[-1].lower()))
  t["last_word_approx"]=last in o or difflib.SequenceMatcher(None,last,o[-len(last)-2:],autojunk=False).ratio()>0.65
  print("ASR_QA",t["index"],score,txt,flush=True)
  if score<0.24:raise RuntimeError("ASR severely diverges on line "+str(t["index"])+": "+txt)
assert len(list(OUT.glob("turn_*.wav")))==28
manifest={"title":"73세 아버지가 매일 밤 영어를 공부하던 진짜 이유",
          "voice_provider":"Gemini 2.5 Flash TTS","voices":VOICE,
          "turns":out,"raw_seconds":round(sum(t["seconds"] for t in out),3),
          "post_speed":1.25,
          "complete_line_wav":True,
          "subtitle_method":"Audio segment duration is authoritative; individual subtitle lines use each source audio interval."}
(OUT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf8")
print("AUDIO_PACKAGE_OK",len(out),"SILENCE_SAFE_SECONDS",manifest["raw_seconds"],flush=True)
