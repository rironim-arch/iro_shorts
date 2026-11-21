#!/usr/bin/env python3
import os,re,time,wave,subprocess,json
from pathlib import Path
from google import genai
from google.genai import types
from faster_whisper import WhisperModel
OUT=Path("father_remarriage_narrator_repair");OUT.mkdir(exist_ok=True)
LINE="아버지는 다시 배드민턴장으로 향했습니다. 운동을 마친 뒤, 두 사람은 나란히 걸으며 다음 여행을 이야기했습니다."
PROMPT=(
"Speak in Korean with the Gemini Kore female storyteller voice, matching a mature, warm, calm narration. "
"Read the entire two-sentence passage verbatim with no additions. It MUST finish with clearly audible '이야기했습니다.' "
"Do not add a CTA or anything else. Natural moderately brisk clear speech, smooth emotional continuity, "
"no unnaturally long pauses, no background music. This is a complete excerpt and should not stop early. "
"Read exactly:\n\n"+LINE)
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
for a in range(4):
 try:
  r=client.models.generate_content(model="gemini-2.5-flash-preview-tts",contents=PROMPT,
   config=types.GenerateContentConfig(response_modalities=["AUDIO"],speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")))))
  pkt=next(p.inline_data for c in r.candidates for p in c.content.parts if getattr(p,"inline_data",None) and getattr(p.inline_data,"data",None))
  break
 except Exception as e:
  print("TTS_RETRY",a,str(e)[:250],flush=True)
  if a==3:raise
  time.sleep(7)
raw=OUT/"new_narration_raw.wav"
if pkt.data.startswith(b"RIFF"):raw.write_bytes(pkt.data)
else:
 m=re.search(r"rate=(\d+)",pkt.mime_type or "")
 with wave.open(str(raw),"wb") as w:
  w.setnchannels(1);w.setsampwidth(2);w.setframerate(int(m.group(1)) if m else 24000);w.writeframes(pkt.data)
clean=OUT/"new_narration_kore.wav"
subprocess.run(["ffmpeg","-y","-v","error","-i",str(raw),"-af","loudnorm=I=-17:TP=-2:LRA=10",
 "-ar","24000","-ac","1",str(clean)],check=True)
with wave.open(str(clean)) as w: duration=w.getnframes()/w.getframerate()
model=WhisperModel("small",device="cpu",compute_type="int8",cpu_threads=4,num_workers=2)
segs,_=model.transcribe(str(clean),language="ko",beam_size=4,vad_filter=False,condition_on_previous_text=False)
transcript=" ".join(s.text.strip() for s in segs)
print("ASR_REPAIRED",transcript,round(duration,3),flush=True)
norm=lambda s:re.sub(r"[^가-힣]","",s)
if not all(x in norm(transcript) for x in ["아버지는","배드민턴장","운동을마친뒤","다음여행을","이야기했습니다"]):
 raise RuntimeError("Voice missing required text; do NOT publish")
(OUT/"qa.json").write_text(json.dumps({"expected":LINE,"asr":transcript,"seconds":duration,"voice":"Gemini Kore","ending_complete":True,"final_words":"다음 여행을 이야기했습니다."},ensure_ascii=False,indent=2),encoding="utf8")
print("ALL_WORDS_VERIFIED",flush=True)
