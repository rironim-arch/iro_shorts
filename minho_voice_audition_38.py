#!/usr/bin/env python3
"""Audition 8 Gemini voices in Korean: 6 alternative casting voices + 2 old baselines.
Uses Gemini 3.8 Flash TTS v1beta, turn-level speech metadata and no audio speed changes.
"""
import os, json, base64, subprocess, time, difflib, re, wave
from pathlib import Path
from google import genai
from google.genai import types
out=Path("minho_voice_auditions")
out.mkdir(exist_ok=True)
voices=[
 {"name":"Umbriel","role":"민호","style":"A tired but warm middle-aged Korean man quietly admitting loneliness. Natural conversational pacing, not stage acting. Restrained and hesitant, with small authentic pauses."},
 {"name":"Algenib","role":"민호","style":"A slightly rough voiced middle-aged Korean man, emotionally reserved, speaking to a friend for the first time about his loneliness. Natural conversation and restrained feeling, no theatrical sobbing."},
 {"name":"Zubenelgenubi","role":"민호","style":"A 53-year-old ordinary Korean man, unpolished conversational expression and slight embarrassment. He is candid and sincere. Speak naturally with light hesitation, do not overact."},
 {"name":"Sulafat","role":"내레이션","style":"A warm Korean female storyteller, soft and restrained. Narrate a poignant real-life story at a natural pace, conveying subtext, avoiding promotional intonation and exaggerated melodrama."},
 {"name":"Gacrux","role":"내레이션","style":"A mature Korean female documentary narrator. Warm, plainspoken and emotionally grounded; natural breaths and a calm thoughtful pace rather than formal newsreading."},
 {"name":"Vindemiatrix","role":"내레이션","style":"A gentle Korean female narrator telling a personal story with empathy and conversational clarity, subtle sadness, balanced pauses, no theatrical affect."},
 {"name":"Orus","role":"민호_기존","style":"A 53-year-old everyday Korean man, gentle but hurt, telling a friend about loneliness, relaxed natural pace without shouting."},
 {"name":"Kore","role":"내레이션_기존","style":"A warm Korean female storyteller, understated empathy and a steady natural storytelling cadence."}
]
men="나, 술자리에 가면 늘 웃거든. 근데 집에만 오면... 이상하게 더 외로워. 그냥 혼자 있는 게 무서웠던 걸까?"
women="쉰세 살 민호에게는 모임이 다섯 개나 있었습니다. 술자리에서는 늘 웃었지만, 집에 돌아오면 아무에게도 전화할 수 없었죠."
client=genai.Client(http_options={"api_version":"v1beta"},api_key=os.environ["GEMINI_API_KEY"])
def shell(cmd):
 p=subprocess.run(cmd,capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stderr[-600:])
return_items=[]
for i,v in enumerate(voices):
 name=v["name"]
 line=men if "민호" in v["role"] else women
 file=out/f"{i+1:02d}_{name}.wav"
 sample=out/f"{i+1:02d}_{name}.mp3"
 for attempt in range(4):
  try:
   response=client.interactions.create(
      model="gemini-3.8-flash-tts",
      input=[{"type":"user_input","content":[{"type":"text","text":line,
        "annotations":[{"type":"speech_metadata","style":v["style"]}]}]}],
      response_format={"type":"audio"},
      generation_config={"speech_config":[{"voice":name}]})
   d=response.output_audio.data
   if not d:raise ValueError("No audio data")
   b=base64.b64decode(d) if isinstance(d,str) else d
   if b[:4]==b"RIFF":file.write_bytes(b)
   else:
    with wave.open(str(file),"wb") as w:
      w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(b)
   # mp3 unchanged rate, reasonable loudness; preserve full syllables.
   shell(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(file),
     "-af","loudnorm=I=-18:TP=-1.5:LRA=9",
     "-c:a","libmp3lame","-b:a","128k",str(sample)])
   with wave.open(str(file)) as w:dur=w.getnframes()/w.getframerate()
   if dur<3 or dur>26:raise RuntimeError(f"Bad duration {dur:.1f}")
   record={"name":name,"role":v["role"],"prompt_style":v["style"],"text":line,"duration":round(dur,2),"mp3":sample.name,"wav":file.name,"model":"gemini-3.8-flash-tts"}
   return_items.append(record)
   print("SAMPLE_OK",name,v["role"],round(dur,2),sample.name,flush=True)
   break
  except Exception as exc:
   print("RETRY",name,attempt,str(exc)[:450],flush=True)
   if attempt==3:raise
   time.sleep(12+attempt*15)
 time.sleep(9)
(out/"manifest.json").write_text(json.dumps(return_items,ensure_ascii=False,indent=2),encoding="utf8")
print("FINAL",len(return_items),flush=True)
