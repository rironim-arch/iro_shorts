#!/usr/bin/env python3
"""Repair two truncated father lines at source, assert endings via Korean ASR."""
import os,re,time,wave,json,subprocess
from pathlib import Path
from google import genai
from google.genai import types
from faster_whisper import WhisperModel
OUT=Path("father_two_endings_repair");OUT.mkdir(exist_ok=True)
LINES=[
"내가 혼자 밥을 먹는지, 어디 아픈 데는 없는지, 마지막으로 물어본 게 언제였냐.",
"네 엄마를 보내고도 오래 버텼다. 그런데 말이다, 혼자 늙어 간다는 게… 생각보다 외롭더라."
]
VOICESTYLE=("You are a natural believable Korean father in his seventies, speaking with Gemini Enceladus. "
"Low and soft, expressive without any shouting or theatrical old-age imitation. "
"Voice style consistent with a mature Korean man speaking to his son, emotionally wounded but controlled. "
"Deliver the Korean sentence without altering or omitting words. "
"Especially finish the last clause and last syllable naturally. "
"No music, sound effects, introduction or spoken instructions. "
"Use clear conversational Korean, do not pause more than half a second between sentences. "
"Read ONLY this paragraph:\n\n")
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
for i,text in enumerate(LINES):
 pkt=None
 for attempt in range(4):
  try:
   res=client.models.generate_content(model="gemini-2.5-flash-preview-tts",contents=VOICESTYLE+text,
     config=types.GenerateContentConfig(response_modalities=["AUDIO"],speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
      prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Enceladus")))))
   for c in res.candidates:
    for p in c.content.parts:
     d=getattr(p,"inline_data",None)
     if d is not None and getattr(d,"data",None):pkt=d;break
    if pkt:break
   if pkt is None:raise RuntimeError("TTS no audio")
   break
  except Exception as e:
   print("RETRY",i,attempt,str(e)[:220],flush=True)
   if attempt==3:raise
   time.sleep(7*(attempt+1))
 raw=OUT/f"father_{i}_raw.wav"
 if pkt.data.startswith(b"RIFF"):raw.write_bytes(pkt.data)
 else:
  m=re.search(r"rate=(\d+)",pkt.mime_type or "")
  with wave.open(str(raw),"wb") as w:
   w.setnchannels(1);w.setsampwidth(2);w.setframerate(int(m.group(1)) if m else 24000);w.writeframes(pkt.data)
 dst=OUT/f"father_{i}_full.wav"
 subprocess.run(["ffmpeg","-y","-v","error","-i",str(raw),"-af","loudnorm=I=-17:TP=-2:LRA=10",
   "-ar","24000","-ac","1",str(dst)],check=True)
 with wave.open(str(dst)) as w:dur=w.getnframes()/w.getframerate()
 print("GENERATED",i,dur,flush=True)
model=WhisperModel("small",device="cpu",compute_type="int8",cpu_threads=4,num_workers=2)
report=[]
for i,line in enumerate(LINES):
 audio=OUT/f"father_{i}_full.wav"
 s,_=model.transcribe(str(audio),language="ko",word_timestamps=True,beam_size=4,condition_on_previous_text=False,vad_filter=False)
 s=list(s);spoken=" ".join(seg.text.strip() for seg in s)
 words=[w for seg in s for w in (seg.words or [])]
 observed=re.sub(r"[^가-힣]","",spoken)
 end_token=["언제였냐","외롭더라"][i]
 print("CHECK",i,spoken,"END_CHECK",end_token in observed,flush=True)
 if end_token not in observed:raise RuntimeError("End of father phrase is missing: "+str(i)+" "+spoken)
 item={"original":line,"transcribed":spoken,"last_word_check":end_token,
   "last_word_confirmed":True,"end_word_at":words[-1].end if words else None}
 report.append(item)
(OUT/"qa.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
print("BOTH_FATHER_ENDINGS_ASR_VERIFIED",flush=True)
