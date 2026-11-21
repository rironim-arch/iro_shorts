#!/usr/bin/env python3
import os,re,time,wave,json,subprocess,difflib,unicodedata
from pathlib import Path
from google import genai
from google.genai import types
from faster_whisper import WhisperModel
OUT=Path("father_remarriage_audio");OUT.mkdir(exist_ok=True)
TURNS=[["son","아버지, 재혼은 하셔도 됩니다. 하지만 혼인신고는 절대 안 돼요."],["narrator","일흔을 넘긴 아버지 앞에 아들이 종이 한 장을 내밀었습니다. 재혼 상대에게 재산을 넘기지 않고 혼인신고도 하지 않겠다는 각서였습니다."],["narrator","아버지는 몇 년 전 아내를 먼저 떠나보냈습니다. 혼자 밥을 먹고, 혼자 텔레비전을 보며 하루하루를 보냈죠."],["narrator","그러다 배드민턴 동호회에서 비슷한 나이의 여성을 만났습니다. 운동이 끝나면 함께 차를 마셨고, 주말이면 가까운 곳으로 나들이도 다녔습니다."],["narrator","아버지는 오랜만에 웃는 날이 많아졌습니다. 그리고 어느 날, 아들에게 조심스럽게 말을 꺼냈죠."],["father","운동 끝나고 같이 차 마실 사람이 생겼다. 나, 그분하고 결혼할 생각이다."],["narrator","하지만 아들 내외의 표정은 순식간에 굳어졌습니다."],["son","아버지, 그분에 대해 얼마나 아세요? 정말 아버지를 좋아하는지 어떻게 알아요?"],["father","그 사람, 참 따뜻한 사람이다. 너도 만나 보면 알 거야."],["son","아버지 명의 집도 있고 통장도 있잖아요. 나중에 재산 문제 생기면 어떡해요?"],["narrator","며칠 뒤, 아들은 며느리와 함께 다시 찾아왔습니다. 손에는 서류 한 장이 들려 있었죠."],["son","여기 각서예요. 재산은 자식들에게만 남기고 혼인신고는 하지 않겠다고 써 주세요."],["narrator","아버지는 서류를 읽다가 손을 멈췄습니다. 그리고 천천히 아들을 바라봤습니다."],["father","너는 내가 걱정되는 거냐, 아니면 이 집이 걱정되는 거냐?"],["son","아버지, 그렇게 말씀하시면 섭섭하죠. 다 아버지 생각해서 그러는 건데."],["father","내가 혼자 밥을 먹는지, 어디 아픈 데는 없는지, 마지막으로 물어본 게 언제였냐."],["narrator","아들은 아무 말도 하지 못했습니다."],["father","네 엄마를 보내고도 오래 버텼다. 그런데 말이다, 혼자 늙어 간다는 게… 생각보다 외롭더라."],["son","아버지…"],["father","재산 문제는 내가 알아서 잘 정리하마. 하지만 남은 인생, 누구와 보낼지는 내가 결정하겠다."],["narrator","아버지는 각서에 서명하지 않았습니다. 대신 다음 날, 오래 묵혀 두었던 여행 가방을 꺼냈습니다."],["father","내가 너희 아버지로 산 세월도 소중했다. 하지만 이제는, 나 자신으로도 좀 살아 보고 싶구나."],["narrator","아버지는 다시 배드민턴장으로 향했습니다. 운동을 마친 뒤, 두 사람은 나란히 걸으며 다음 여행을 이야기했습니다."],["father","이 나이에… 다시 봄이 올 줄은 몰랐네."],["narrator","이 이야기가 마음에 남으셨다면 구독과 좋아요 부탁드립니다."]]
VOICES={"narrator":"Kore","father":"Algenib","son":"Orus"}
NOTES={
"narrator":"Warm mature Korean female storyteller with subtle suspense, natural pace, and tender restrained ending.",
"father":"Realistic seventy-year-old Korean man, deep, slightly gravelly and breathy; first hopeful, then wounded, finally quietly resolute. No exaggerated elder impersonation, never shout. SAME voice identity throughout.",
"son":"Korean forty-year-old male, practical and firm, becoming defensively anxious. Natural spoken Korean, clear and never cartoonish. SAME voice identity throughout."
}
def sh(*a):subprocess.run(list(map(str,a)),check=True)
def norm(s):return re.sub(r"[^가-힣a-z0-9]","",unicodedata.normalize("NFKC",s)).lower()
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
sources={}
for role,voice in VOICES.items():
 lines=[t for r,t in TURNS if r==role]
 prompt=(f"Act in Korean: {NOTES[role]} Read the following Korean paragraphs exactly, all of them, in ONE CONTINUOUS TAKE. Keep same voice timbre, microphone distance, volume. Give a distinct brief pause between paragraphs so they can be split afterward. Never say labels, paragraph numbers, instructions. No music or effects. Say the final phrase fully and clearly. The complete script follows:\n\n"+"\n\n".join(lines))
 pkt=None
 for attempt in range(4):
  try:
   r=client.models.generate_content(model="gemini-2.5-flash-preview-tts",
     contents=prompt,config=types.GenerateContentConfig(response_modalities=["AUDIO"],
     speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
       prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)))))
   for c in r.candidates:
    for p in c.content.parts:
     q=getattr(p,"inline_data",None)
     if q is not None and getattr(q,"data",None):pkt=q;break
    if pkt is not None:break
   if pkt is None:raise RuntimeError("No audio")
   break
  except Exception as e:
   print("TTS_RETRY",role,attempt,str(e)[:250],flush=True)
   if attempt==3:raise
   time.sleep(7*(attempt+1))
 raw=OUT/f"{role}_raw.wav"
 if pkt.data.startswith(b"RIFF"):raw.write_bytes(pkt.data)
 else:
  m=re.search(r"rate=(\d+)",pkt.mime_type or "")
  with wave.open(str(raw),"wb") as w:
   w.setnchannels(1);w.setsampwidth(2);w.setframerate(int(m.group(1)) if m else 24000);w.writeframes(pkt.data)
 clean=OUT/f"{role}_continuous.wav"
 sh("ffmpeg","-y","-v","error","-i",raw,
    "-af","loudnorm=I=-17:TP=-2:LRA=10","-ar","24000","-ac","1",clean)
 with wave.open(str(clean)) as w:duration=w.getnframes()/w.getframerate()
 sources[role]=(clean,duration,lines)
 print("GEMINI_ONE_TAKE",role,voice,round(duration,3),len(lines),flush=True)
print("ASR_START",flush=True)
whisper=WhisperModel("small",device="cpu",compute_type="int8",cpu_threads=4,num_workers=2)
parts={}; reports={}
for role,(f,duration,lines) in sources.items():
 segs,_=whisper.transcribe(str(f),language="ko",word_timestamps=True,beam_size=4,
     condition_on_previous_text=False,vad_filter=False)
 segs=list(segs)
 words=[{"word":w.word,"start":float(w.start),"end":float(w.end)} for s in segs
        for w in (s.words or []) if w.word.strip()]
 rec=" ".join(s.text.strip() for s in segs)
 (OUT/f"{role}_asr.txt").write_text(rec,encoding="utf8")
 expected=[(i,norm(w)) for i,line in enumerate(lines) for w in line.split() if norm(w)]
 seen=[norm(w["word"]) for w in words]
 match=difflib.SequenceMatcher(None,[s for _,s in expected],seen,autojunk=False)
 m={}
 for b in match.get_matching_blocks():
  for k in range(b.size):m[b.a+k]=b.b+k
 ratio=sum(len(expected[i][1]) for i in m)/max(1,sum(len(x[1]) for x in expected))
 print("ASR_MATCH",role,round(ratio,3),len(words),flush=True)
 if ratio<0.23 or len(words)<2*len(lines):raise RuntimeError("Audio ASR did not sufficiently match script: "+role)
 anchors={0:0.,len(expected):duration}
 for i,j in m.items():anchors[i]=words[j]["start"]
 aa=sorted(anchors.items())
 def interp(i):
  for (a,ta),(b,tb) in zip(aa,aa[1:]):
   if a<=i<=b:return ta+(i-a)*(tb-ta)/max(1,b-a)
  return duration
 bounds=[0.]
 for li in range(1,len(lines)):
  x=next(j for j,(n,_) in enumerate(expected) if n==li)
  bounds.append(max(0,interp(x)-.06))
 bounds.append(duration)
 for li in range(len(lines)):
  start=max(0,bounds[li]-(.03 if li else 0))
  length=bounds[li+1]-start
  if length<.45:raise RuntimeError(f"Bad chunk {role}:{li} {length}")
  out=OUT/f"{role}_{li:02}.wav"
  sh("ffmpeg","-y","-v","error","-ss",f"{start:.4f}","-i",f,"-t",f"{length:.4f}","-ar","24000","-ac","1",out)
  parts[(role,li)]=(out,length)
 reports[role]={"voice":VOICES[role],"duration":duration,"original_tts_calls":1,
                "utterances":len(lines),"asr_exact_token_coverage":ratio,"transcribed":rec}
if not all(t in norm(reports["narrator"]["transcribed"]) for t in ["구독","좋아요","부탁"]):
 raise RuntimeError("Final CTA was NOT audibly verified by ASR")
seq=[]; idx={r:0 for r in VOICES}
for i,(role,txt) in enumerate(TURNS):
 j=idx[role];idx[role]+=1
 f,d=parts[(role,j)]
 seq.append({"index":i,"role":role,"voice":VOICES[role],"line":txt,"file":f.name,"duration":round(d,4)})
(OUT/"turn_manifest.json").write_text(json.dumps({
 "turns":seq,"voices":reports,
 "quality_control":{"three_consistent_source_takes":True,"Gemini_TTS_calls":3,
   "CTA_ASR_verified":True,"requires_human_listening_review":True}
},ensure_ascii=False,indent=2),encoding="utf8")
print("THREE_VOICE_AUDIO_READY",len(seq),round(sum(x["duration"] for x in seq),2),flush=True)
