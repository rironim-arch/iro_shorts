#!/usr/bin/env python3
"""Replace old Algenib father with Gemini Enceladus in ONE continuous take."""
import os,re,time,wave,json,subprocess,difflib,unicodedata
from pathlib import Path
from google import genai
from google.genai import types
from faster_whisper import WhisperModel
OUT=Path("father_enkel_voice");OUT.mkdir(exist_ok=True)
LINES=["운동 끝나고 같이 차 마실 사람이 생겼다. 나, 그분하고 결혼할 생각이다.","너는 내가 걱정되는 거냐, 아니면 이 집이 걱정되는 거냐?","내가 혼자 밥을 먹는지, 어디 아픈 데는 없는지, 마지막으로 물어본 게 언제였냐.","네 엄마를 보내고도 오래 버텼다. 그런데 말이다, 혼자 늙어 간다는 게… 생각보다 외롭더라.","재산 문제는 내가 알아서 잘 정리하마. 하지만 남은 인생, 누구와 보낼지는 내가 결정하겠다.","내가 너희 아버지로 산 세월도 소중했다. 하지만 이제는, 나 자신으로도 좀 살아 보고 싶구나.","이 나이에… 다시 봄이 올 줄은 몰랐네."]
def norm(s):return re.sub(r"[^가-힣a-z0-9]","",unicodedata.normalize("NFKC",s)).lower()
prompt=(
 "You are a skilled mature Korean MALE actor, a believable elderly father in his seventies. "
 "Use Gemini Enceladus consistently. Sound lower-pitched, naturally aged and softly breathy, with an unforced Korean elder's voice and slightly weathered warmth. "
 "Do NOT fake a rasp, a cartoonish tremble, or elderly caricature. No excessive crying or shouting. "
 "Performance progression: hope and shyness; deeply hurt quiet question; disappointed confession; years of lonely grief; firm dignified decision; tender resolve; a small smile of gratitude. "
 "Read the following seven dialogue excerpts as ONE CONTINUOUS RECORDING in the same stable voice identity and microphone proximity. "
 "Read only Korean dialogue verbatim, with a clear short 0.5-second silence between each paragraph to allow precise editing. "
 "Do not announce numbers, punctuation or labels. Do not add anything. Finish the last syllable fully.\n\n" + "\n\n".join(LINES)
)
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
packet=None
for attempt in range(4):
 try:
  reply=client.models.generate_content(model="gemini-2.5-flash-preview-tts",contents=prompt,
   config=types.GenerateContentConfig(response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
     prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Enceladus")))))
  for can in reply.candidates:
   for part in can.content.parts:
    dat=getattr(part,"inline_data",None)
    if dat and getattr(dat,"data",None):packet=dat;break
   if packet:break
  if packet is None:raise RuntimeError("Empty Enceladus audio")
  break
 except Exception as e:
  print("TTS_ERROR",attempt,str(e)[:250],flush=True)
  if attempt==3:raise
  time.sleep(7*(attempt+1))
raw=OUT/"father_raw.wav"
if packet.data.startswith(b"RIFF"):raw.write_bytes(packet.data)
else:
 m=re.search(r"rate=(\d+)",packet.mime_type or "")
 with wave.open(str(raw),"wb") as w:
  w.setnchannels(1);w.setsampwidth(2);w.setframerate(int(m.group(1)) if m else 24000);w.writeframes(packet.data)
master=OUT/"father_Enceladus_original.wav"
subprocess.run(["ffmpeg","-y","-v","error","-i",str(raw),"-af","loudnorm=I=-17:TP=-2:LRA=10","-ar","24000","-ac","1",str(master)],check=True)
with wave.open(str(master)) as w:duration=w.getnframes()/w.getframerate()
if not 15<duration<120:raise RuntimeError("Bad TTS runtime "+str(duration))
print("ENKEL_ONE_TAKE",duration,flush=True)
model=WhisperModel("small",device="cpu",compute_type="int8",cpu_threads=4,num_workers=2)
segments,_=model.transcribe(str(master),language="ko",word_timestamps=True,beam_size=4,condition_on_previous_text=False,vad_filter=False)
segments=list(segments)
words=[{"word":w.word,"start":float(w.start),"end":float(w.end)}
 for s in segments for w in (s.words or []) if w.word.strip()]
spoken=" ".join(x.text for x in segments)
(OUT/"asr_transcript.txt").write_text(spoken,encoding="utf8")
expected=[(i,norm(s)) for i,line in enumerate(LINES) for s in line.split() if norm(s)]
actual=[norm(w["word"]) for w in words]
matcher=difflib.SequenceMatcher(None,[w for i,w in expected],actual,autojunk=False)
mapping={}
for block in matcher.get_matching_blocks():
 for j in range(block.size):mapping[block.a+j]=block.b+j
ratio=sum(len(expected[i][1]) for i in mapping)/max(1,sum(len(x[1]) for x in expected))
if ratio<.35:raise RuntimeError(f"ASR coverage insufficient {ratio:.3f}")
if not all(p in norm(spoken) for p in ["이","나이에","다시","봄이","올","줄"]):
 print("LAST_LINE_ASR_WARNING",spoken[-100:],flush=True)
anchors={0:0.0,len(expected):duration}
for i,j in mapping.items():anchors[i]=words[j]["start"]
aa=sorted(anchors.items())
def interp(i):
 for (i0,t0),(i1,t1) in zip(aa,aa[1:]):
  if i0<=i<=i1:return t0+(i-i0)*(t1-t0)/max(1,i1-i0)
 return duration
bounds=[0.]
for k in range(1,len(LINES)):
 i=next(pos for pos,(li,w) in enumerate(expected) if li==k)
 bounds.append(max(0,interp(i)-.07))
bounds.append(duration)
report=[]
for i,line in enumerate(LINES):
 start=max(0.,bounds[i]-(.02 if i>0 else 0))
 end=bounds[i+1]
 if end-start<.5:raise RuntimeError("TTS paragraph segmentation too short")
 fname=OUT/f"father_{i:02d}.wav"
 subprocess.run(["ffmpeg","-y","-v","error","-ss",f"{start:.4f}","-i",str(master),"-t",f"{end-start:.4f}","-ar","24000","-ac","1",str(fname)],check=True)
 report.append({"index":i,"text":line,"file":fname.name,"seconds":round(end-start,4)})
(OUT/"verified_voice.json").write_text(json.dumps({"Gemini":"Enceladus","generation_calls":1,"speed":"source natural","duration":duration,
 "asr_coverage":ratio,"full_line_count":len(report),"segments":report,
 "human_ear_verification":"required"},ensure_ascii=False,indent=2),encoding="utf8")
print("FATHER_ENCELADUS_VOICE_READY",len(report),round(ratio,3),flush=True)
