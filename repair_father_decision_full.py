#!/usr/bin/env python3
"""Repair an entire father utterance (not last syllables): verify complete spoken ending."""
import os,re,time,wave,json,subprocess
from pathlib import Path
from google import genai
from google.genai import types
from faster_whisper import WhisperModel
OUT=Path("father_full_lastline_repair"); OUT.mkdir(exist_ok=True)
LINE="재산 문제는 내가 알아서 잘 정리하마. 하지만 남은 인생, 누구와 보낼지는 내가 결정하겠다."
prompt=("Act as a dignified elderly Korean man (about seventy) with Gemini Enceladus voice. "
"You are speaking firmly to your adult son, after a painful family dispute. "
"Be natural, serious, quietly resolved; not a cartoon grandpa, no exaggerated croaking. "
"Deliver the ENTIRE script, particularly the very last syllables '결정하겠다.' completely. "
"Do not add anything before or after, no audio music. "
"Do NOT rush. Pause about 0.25 seconds after the first sentence. "
"At the end hold a complete natural final syllable and then one full second of silence, "
"so that an editor can safely join the next sentence without clipping. "
"Korean script, read precisely:\n\n"+LINE)
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
packet=None
for n in range(4):
 try:
  r=client.models.generate_content(model="gemini-2.5-flash-preview-tts",contents=prompt,config=types.GenerateContentConfig(response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Enceladus")))))
  for c in r.candidates:
   for p in c.content.parts:
    pk=getattr(p,"inline_data",None)
    if pk is not None and getattr(pk,"data",None):packet=pk;break
   if packet:break
  if packet is None:raise RuntimeError("No TTS response")
  break
 except Exception as e:
  print("TTS_RETRY",n,str(e)[:200],flush=True)
  if n==3:raise
  time.sleep(8)
raw=OUT/"father_important_raw.wav"
if packet.data.startswith(b"RIFF"):raw.write_bytes(packet.data)
else:
 m=re.search(r"rate=(\d+)",packet.mime_type or "")
 with wave.open(str(raw),"wb") as w:
  w.setnchannels(1);w.setsampwidth(2);w.setframerate(int(m.group(1)) if m else 24000);w.writeframes(packet.data)
clean=OUT/"father_important_complete.wav"
subprocess.run(["ffmpeg","-y","-v","error","-i",str(raw),"-af","loudnorm=I=-17:TP=-2:LRA=10","-ar","24000","-ac","1",str(clean)],check=True)
with wave.open(str(clean)) as w: duration=w.getnframes()/w.getframerate()
if duration<5 or duration>20:raise RuntimeError(f"Unexpected duration {duration}")
model=WhisperModel("small",device="cpu",compute_type="int8",cpu_threads=4,num_workers=2)
segs,_=model.transcribe(str(clean),language="ko",beam_size=4,vad_filter=False,word_timestamps=True,condition_on_previous_text=False)
segs=list(segs)
recognized=" ".join(s.text.strip() for s in segs)
observed=re.sub(r"[^가-힣]","",recognized)
if not ("남은인생" in observed and "누구와" in observed and "결정하겠다" in observed):
 raise RuntimeError(f"The required conclusion has not been recognized: {recognized}")
words=[w for seg in segs for w in (seg.words or []) if w.word.strip()]
ending=words[-1].end if words else duration
out={"text":LINE,"transcript":recognized,"voice":"Gemini Enceladus",
 "last_phrase_confirmed":True,"audio_duration":duration,"recognized_last_word_end":ending,"audio_tail_sec":duration-ending}
(OUT/"qa.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf8")
print("FULL_FATHER_SENTENCE_VERIFIED",json.dumps(out,ensure_ascii=False),flush=True)
