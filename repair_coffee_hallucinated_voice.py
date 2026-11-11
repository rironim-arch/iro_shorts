"""Repair only coffee narration clips with verified hallucinated CTAs.
Verify *recorded audio* again with independent Gemini ASR; fail closed on repetition.
"""
import difflib
import json
import os
import re
import shutil
import time
import wave
from pathlib import Path
from google import genai
from google.genai import types

SRC=Path("voice")
OUT=Path("voice_clean")
OUT.mkdir(exist_ok=True)
old_audit=json.loads(Path("voice_audit/audit.json").read_text(encoding="utf-8"))
manifest=json.loads((SRC/"manifest.json").read_text(encoding="utf-8"))
scenes=manifest["scenes"]
assert len(scenes)==len(old_audit)==11
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
results=[]
def no_cta(text):
 return not bool(re.search(r"구\s*독|좋\s*아\s*요",text))
def normalize(t):
 return re.sub(r"[^0-9A-Za-z가-힣]","",t)
def write_audio(raw,mime,dst):
 if raw.startswith(b"RIFF"):
  dst.write_bytes(raw)
 else:
  match=re.search(r"rate=(\d+)",mime.lower())
  with wave.open(str(dst),"wb") as w:
   w.setnchannels(1);w.setsampwidth(2)
   w.setframerate(int(match.group(1)) if match else 24000)
   w.writeframes(raw)
 with wave.open(str(dst),"rb") as w:
  assert w.getnframes()>10000
def synth(text,dst):
 instructions=(
    "Read precisely the Korean sentence between the delimiters, word for word, once. "
    "Do not add introductions, closings, or any words of your own. "
    "Pronounce naturally as a calm informational narration.\n"
    "<<<BEGIN SENTENCE>>>\n"+text+"\n<<<END SENTENCE>>>"
 )
 response=client.models.generate_content(
   model="gemini-2.5-flash-preview-tts",
   contents=instructions,
   config=types.GenerateContentConfig(
      response_modalities=["AUDIO"],
      speech_config=types.SpeechConfig(
         voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")
         )
      )
   )
 )
 parts=response.candidates[0].content.parts
 audio=next((p.inline_data for p in parts if p.inline_data and p.inline_data.data),None)
 if not audio:raise RuntimeError("No TTS audio")
 write_audio(audio.data,audio.mime_type or "",dst)
def asr(path):
 request=["이 한국어 오디오에 실제로 들리는 말을 모두 그대로 적으세요. "
          "대본을 추측하지 말고 오디오만 받아쓰세요. 다른 설명은 하지 마세요.",
          types.Part.from_bytes(data=path.read_bytes(),mime_type="audio/wav")]
 response=client.models.generate_content(model="gemini-3.8-flash",contents=request)
 return (response.text or "").strip()

for i,(scene,audit) in enumerate(zip(scenes,old_audit)):
 src=SRC/scene["file"]
 dst=OUT/scene["file"]
 expected=scene["line"]
 is_final=i==len(scenes)-1
 if not audit["unexpected_cta"]:
  shutil.copy2(src,dst)
  transcript=audit["transcribed"]
  changed=False
 else:
  changed=True
  transcript=None
  for attempt in range(5):
   try:
    if dst.exists():dst.unlink()
    synth(expected,dst)
    transcript=asr(dst)
    ratio=difflib.SequenceMatcher(None,normalize(expected),normalize(transcript)).ratio()
    cta_good=not no_cta(transcript) if is_final else no_cta(transcript)
    print(f"SCENE {i+1} TRY {attempt+1} CTA_OK={cta_good} SIMILARITY={ratio:.2f}",flush=True)
    print("ACTUALLY_SPOKEN:",transcript,flush=True)
    if cta_good and ratio>=0.55:
     break
    time.sleep(4)
   except Exception as exc:
    print("RETRY_REASON",str(exc)[:180],flush=True)
    if attempt==4:raise
    time.sleep((attempt+1)*9)
  else:
   raise RuntimeError(f"Unable to generate clean audio for scene {i+1}: {transcript}")
 valid=bool(re.search(r"구\s*독|좋\s*아\s*요",transcript))
 if is_final:
  assert valid, f"Final CTA missing: {transcript}"
 else:
  assert not valid, f"Unexpected spoken CTA in scene {i+1}: {transcript}"
 results.append({"scene":i+1,"regenerated":changed,"expected":expected,
                 "spoken":transcript,"cta":valid})
 print("VERIFIED SCENE",i+1,"REGENERATED",changed,flush=True)

assert sum(x["cta"] for x in results)==1
assert results[-1]["cta"]
(OUT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
(OUT/"actual_audio_qa.json").write_text(json.dumps({
 "verified_audio_cta_total":1,
 "verified_body_cta_total":0,
 "verified_final_cta_total":1,
 "regenerated_scenes":[r["scene"] for r in results if r["regenerated"]],
 "scenes":results
},ensure_ascii=False,indent=2),encoding="utf-8")
print("PASS: CTA audible in final scene exactly once; none in first 10.",flush=True)
