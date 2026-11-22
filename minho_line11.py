import os,wave,re,subprocess,time
from pathlib import Path
from google import genai
from google.genai import types
from faster_whisper import WhisperModel
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
line="나 요즘… 집에 가면 좀 외롭더라."
out=Path("minho_single_fix");out.mkdir(exist_ok=True)
model=WhisperModel("base",device="cpu",compute_type="int8",cpu_threads=4)
for i in range(8):
 try:
  r=client.models.generate_content(model="gemini-2.5-flash-preview-tts",
   contents="You are Orus, a Korean man aged 53, stocky, lonely but sincere, softly opening up to his friends over drinks. Read EXACTLY one sentence in Korean. Do NOT say any other words before or after. Fully finish each syllable, including the last one, before silence.\nSCRIPT:\n"+line,
   config=types.GenerateContentConfig(response_modalities=["AUDIO"],speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Orus")))))
  audio=next(p.inline_data for c in r.candidates for p in c.content.parts if getattr(p,"inline_data",None) and getattr(p.inline_data,"data",None))
  raw=out/"raw.wav"
  if audio.data[:4]==b"RIFF":raw.write_bytes(audio.data)
  else:
   ma=re.search(r"rate=(\d+)",audio.mime_type or "")
   with wave.open(str(raw),"wb") as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(int(ma.group(1)) if ma else 24000);w.writeframes(audio.data)
  chunks,_=model.transcribe(str(raw),language="ko",beam_size=3,condition_on_previous_text=False)
  heard=" ".join(c.text.strip() for c in chunks)
  print("ASR",heard,flush=True)
  if "외롭" not in heard or "집" not in heard:raise RuntimeError("ASR doesn't match expected sentence")
  q=subprocess.run(["ffmpeg","-y","-v","error","-i",str(raw),"-af","loudnorm=I=-18:TP=-2:LRA=8,apad=pad_dur=0.24","-ar","24000","-ac","1",str(out/"turn_11.wav")],capture_output=True,text=True)
  if q.returncode:raise RuntimeError(q.stderr)
  with wave.open(str(out/"turn_11.wav")) as w:print("FIX_OK",w.getnframes()/w.getframerate(),flush=True)
  break
 except Exception as e:
  print("RETRY",i,str(e)[:250],flush=True)
  if i==7:raise
  time.sleep(60)
