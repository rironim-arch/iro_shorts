#!/usr/bin/env python3
"""Minho feeling lonely among busy gatherings; complete Gemini TTS source audio with ASR."""
import os,re,time,wave,json,subprocess,difflib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from google import genai
from google.genai import types
TURNS=[{"r":"narrator","s":0,"t":"모임이 다섯 개인 남자. 그런데 집에만 오면 더 외로웠습니다."},{"r":"narrator","s":0,"t":"쉰세 살 민호는 일주일에 다섯 번씩 술자리에 나갔습니다."},{"r":"narrator","s":1,"t":"동창회, 등산 모임, 동네 친목회. 한 번도 빠지지 않았죠."},{"r":"friend","s":0,"t":"민호 형! 내일도 나올 거죠?"},{"r":"minho","s":0,"t":"그럼! 나 빠지면 재미없잖아."},{"r":"narrator","s":1,"t":"듣기 싫은 농담에도 웃고, 생일과 술값까지 챙겼죠."},{"r":"narrator","s":2,"t":"하지만 그 속에서 민호는 자꾸만 작아졌습니다."},{"r":"narrator","s":3,"t":"집에 돌아오면 말 한마디 섞을 사람이 없었습니다."},{"r":"narrator","s":4,"t":"단체방엔 메시지가 일흔 개. 그의 안부를 묻는 말은 없었습니다."},{"r":"minho","s":4,"t":"다들 나를 좋아하는 줄 알았는데..."},{"r":"narrator","s":2,"t":"어느 금요일, 민호는 용기를 내 속마음을 꺼냈습니다."},{"r":"minho","s":2,"t":"나 요즘… 집에 가면 좀 외롭더라."},{"r":"friend","s":2,"t":"에이, 형! 분위기 깨지 말고 한 잔 더 해요."},{"r":"narrator","s":2,"t":"사람들은 다시 웃었습니다. 민호도 따라 웃었습니다."},{"r":"narrator","s":3,"t":"집에 돌아온 그는 젖은 눈으로 연락처를 넘겼습니다."},{"r":"narrator","s":5,"t":"수백 개 이름 중에, 자기 말을 들어줄 사람은 떠오르지 않았죠."},{"r":"minho","s":6,"t":"나는 이 사람들이 좋아서 매달리는 걸까?"},{"r":"minho","s":6,"t":"아니면… 혼자인 내가 초라해 보여서였을까?"},{"r":"narrator","s":6,"t":"다음 날, 처음으로 모임 초대에 오늘은 쉬겠다고 답했습니다."},{"r":"narrator","s":7,"t":"혼자 저녁을 먹었습니다. 텅 빈 식탁이 낯설었습니다."},{"r":"narrator","s":7,"t":"그런데 마음은 이상하게 조용했습니다."},{"r":"minho","s":7,"t":"누구한테 잘 보이려고 웃지 않아도 되는구나."},{"r":"narrator","s":8,"t":"외롭지 않으려고 잡은 관계가, 때로는 나를 더 외롭게 만듭니다."},{"r":"narrator","s":8,"t":"혼자를 견딜 때, 함께하고 싶은 사람을 고를 수 있습니다."},{"r":"cta","s":8,"t":"이 이야기가 마음에 남으셨다면 구독과 좋아요 부탁드립니다."}]
OUT=Path("minho_gemini_audio");OUT.mkdir(exist_ok=True)
VOICES={"narrator":"Kore","minho":"Orus","friend":"Puck","cta":"Kore"}
ROLE={
"narrator":"Korean adult female narrator, professionally clear warm storyteller, reflective but not overdramatic, moderate smooth pace and consistent volume. Express loneliness and reconciliation gently.",
"minho":"Korean male character Minho, 53 years old, stout, middle aged, a little rough/tired but kind. Speak naturally and restrained. Cheerful in first line, quietly lonely later. Use consistent same man's voice for every Minho sentence.",
"friend":"Korean man in his mid 40s, casually cheerful and dismissive at a drinking party. Friendly and loud enough to be heard but not screaming. Natural conversation.",
"cta":"The same adult Korean female narrator voice Kore. Read this one closing call to action in natural warm conversational Korean."
}
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
def shell(*args):
 p=subprocess.run(list(map(str,args)),capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stderr[-450:])
def generate(i,t):
 role=t["r"];line=t["t"];voice=VOICES[role]
 prompt=(ROLE[role]+
 " 한국어 대사 하나를 정확하게 읽으세요. 대사 외 다른 말은 말하지 마세요. "
 "읽는 속도를 일정하게 유지하고, 마지막 글자를 끝까지 정확히 발음한 후 완전히 멈추세요. "
 "불필요한 추임새, 해설, 반복, 허밍이나 교훈 덧붙이기 금지. "
 "Speak all the provided words, with no added words, no paraphrase, no role names, no music; don't cut off the end.\n\n"
 "SCRIPT:\n"+line)
 raw=OUT/f"raw_{i:02d}.wav";final=OUT/f"turn_{i:02d}.wav"
 for k in range(5):
  try:
   r=client.models.generate_content(model="gemini-2.5-flash-preview-tts",
     contents=prompt,config=types.GenerateContentConfig(response_modalities=["AUDIO"],
     speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
      prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)))))
   d=next(x.inline_data for c in r.candidates for x in c.content.parts if getattr(x,"inline_data",None) and getattr(x.inline_data,"data",None))
   if d.data[:4]==b"RIFF":raw.write_bytes(d.data)
   else:
    mtch=re.search(r"rate=(\d+)",d.mime_type or "")
    with wave.open(str(raw),"wb") as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(int(mtch.group(1)) if mtch else 24000);w.writeframes(d.data)
   with wave.open(str(raw),"rb") as w:sec=w.getnframes()/w.getframerate()
   if not .8<sec<16:raise RuntimeError(f"Audio length {sec}")
   shell("ffmpeg","-y","-loglevel","error","-i",raw,"-af",
     "loudnorm=I=-18:TP=-2:LRA=8,apad=pad_dur=0.24","-ar","24000","-ac","1",final)
   with wave.open(str(final),"rb") as w:seconds=w.getnframes()/w.getframerate()
   print("TTS_OK",i,role,voice,round(seconds,3),line,flush=True)
   return dict(index=i,**t,voice=voice,file=final.name,seconds=round(seconds,4),tries=k+1)
  except Exception as e:
   print("RETRY",i,k,str(e)[:160],flush=True)
   if k==4:raise
   time.sleep(4+k*8)
out=[None]*len(TURNS)
with ThreadPoolExecutor(max_workers=3) as ex:
 futures={ex.submit(generate,i,t):i for i,t in enumerate(TURNS)}
 for f in as_completed(futures):out[futures[f]]=f.result()
print("ASR_CHECK_START",flush=True)
from faster_whisper import WhisperModel
asr=WhisperModel("base",device="cpu",compute_type="int8",cpu_threads=4)
for t in out:
 pieces,_=asr.transcribe(str(OUT/t["file"]),language="ko",beam_size=3,condition_on_previous_text=False,vad_filter=False)
 heard=" ".join(p.text.strip() for p in pieces)
 norm=lambda x:re.sub(r"[^가-힣a-z0-9]","",x.lower())
 sim=difflib.SequenceMatcher(None,norm(t["t"]),norm(heard),autojunk=False).ratio()
 t["asr"]=heard;t["asr_match"]=round(sim,3)
 print("ASR_QA",t["index"],round(sim,3),heard,flush=True)
 if sim<.28:raise RuntimeError(f"Unreliable audio line {t['index']} {heard}")
manifest=dict(title="53세 민호가 모임을 다섯 개나 나가면서도 외로웠던 이유",provider="Gemini 2.5 Flash TTS",
 characters=VOICES,turns=out,raw_seconds=round(sum(x["seconds"] for x in out),4),
 caption_sync="Per line start/end of audio after edit; full audio with padded ending",speedup=1.25)
(OUT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf8")
print("AUDIO_OK",manifest["raw_seconds"],len(out),flush=True)
