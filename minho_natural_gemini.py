#!/usr/bin/env python3
"""Generate naturally paced Gemini voices in coherent paragraphs for Minho's loneliness story.
No tempo/atempo changes; avoid per-sentence splices. Exact original source lines kept in JSON.
"""
import os,re,json,wave,time,difflib,subprocess
from pathlib import Path
from google import genai
from google.genai import types
from faster_whisper import WhisperModel
CHUNKS=[{"role":"minho","text":"야, 딱 한 잔만 더 하자. 내가 계산할게.","scene":0},{"role":"narrator","text":"새벽 두 시, 술집이 문을 닫으려는데도 민호는 사람들을 붙잡았습니다. 한 친구가 어색하게 웃었습니다. '형, 우린 내일 출근해야 해요.' 민호도 웃으며 손을 흔들었습니다. 하지만 모두 떠나고 나자, 그 웃음이 사라졌습니다. 쉰세 살 민호에게는 모임이 다섯 개나 있었습니다. 동창 모임, 등산 모임, 동네 친목회. 누구 생일이면 케이크를 들고, 술값이 모자라면 자기 돈으로 채웠습니다. 모임에서 한 번 빠지면 자신을 잊어버릴까 봐 두려웠거든요.","scene":0},{"role":"narrator","text":"모임에선 남의 승진과 집 이야기가 끝없이 오갔습니다. 민호가 자기 얘기를 꺼내면 다른 사람이 말을 끊었죠. 그래도 그는 크게 웃고 술잔을 채웠습니다. 혼자 남는 사람이 되고 싶지 않았습니다. 그날 집에 돌아와 휴대폰을 켰습니다. 단체방에는 메시지가 일흔 개나 쌓여 있었습니다. 그런데 잘 들어갔냐고 묻는 연락은 하나도 없었습니다.","scene":2},{"role":"minho","text":"나랑 술 마실 사람은 이렇게 많은데… 내 얘기를 들어줄 사람은 없구나.","scene":5},{"role":"narrator","text":"다음 토요일에도 모임 초대가 왔습니다. 민호는 '갈게'라고 적었다가 지우기를 몇 번이나 반복했습니다. 집에 혼자 있으면 또 쓸쓸할까 봐 겁이 났습니다. 하지만 이번엔 잠깐 멈췄습니다.","scene":6},{"role":"minho","text":"오늘은 집에서 좀 쉬겠습니다. 다음에 봐요.","scene":6},{"role":"narrator","text":"문자를 보내고도 몇 번이나 휴대폰을 확인했습니다. 자기 없이 더 친해지면 어쩌지. 그런데 생각보다 아무 일도 일어나지 않았습니다. 민호는 조금 서운했고, 조금은 홀가분했습니다. 오랜만에 혼자 밥을 차려 먹었습니다. TV를 끄고 천천히 씹었습니다. 누군가의 비위를 맞추지 않아도 되는 저녁은 생각보다 괜찮았습니다.","scene":6},{"role":"minho","text":"오늘은… 나랑도 좀 있어 봐야겠다.","scene":8},{"role":"narrator","text":"사람이 많다고 외로움이 없어지는 건 아닙니다. 때로는 아무도 붙잡지 않아도 되는 밤이 나를 되찾는 시작일 수 있습니다. 이 이야기가 마음에 남으셨다면 구독과 좋아요 부탁드립니다.","scene":8}]
OUTPUT=Path("minho_natural_audio");OUTPUT.mkdir(exist_ok=True)
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
voice={"narrator":"Kore","minho":"Orus"}
styling={
 "narrator":"You are a female Korean documentary storyteller. Speak as ONE connected natural paragraph with the emotional rhythm of a thoughtful human narrator. Pace approximately natural conversation: not quick, not sluggish. Give phrase breaks and let sentences breathe. Emphasize the embarrassed, lonely, then relieved feelings without sounding preachy. Maintain a consistent warm Kore voice. Do not sing.",
 "minho":"You are Minho, a 53-year-old everyday Korean man, stocky and somewhat awkward. Voice is Orus. You use natural Korean with an ordinary warm middle-aged man's slightly worn timbre. Opening: overeager, hopeful; alone at home: quietly sad; later: gentle, hesitant confidence. Never perform as a cartoon. Let emotional pauses happen without exaggerating."
}
def cn(x):return re.sub(r"[^가-힣a-z0-9]","",x.lower())
def proc(*args):
 p=subprocess.run(list(map(str,args)),capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stderr[-500:])
model=WhisperModel("base",device="cpu",compute_type="int8",cpu_threads=4)
results=[]
for i,d in enumerate(CHUNKS):
 dest=OUTPUT/f"clip_{i:02d}.wav"
 t=d["text"]; r=d["role"]; v=voice[r]
 prompt=(styling[r]+"\n"
 "Read ONLY the exact Korean transcript below in a single connected, unhurried natural performance. "
 "Do NOT add an introduction, summary, role label, background music, or any extra words. "
 "Finish the last syllable fully, then fall silent. Korean natural prosody is more important than duration. "
 "Maintain stable speaking speed and volume; do NOT intentionally rush to fit a video runtime.\n"
 "원고 그대로 읽고 마지막 글자까지 완전히 발음하세요. 대사를 낱개로 끊어 읽지 말고 앞뒤 문맥을 연결해서 읽으세요.\n\n"
 "SCRIPT:\n"+t)
 for attempt in range(6):
  try:
   reply=client.models.generate_content(
       model="gemini-2.5-flash-preview-tts",
       contents=prompt,
       config=types.GenerateContentConfig(response_modalities=["AUDIO"],
       speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
       prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=v)))))
   audio=next(x.inline_data for c in reply.candidates for x in c.content.parts
        if getattr(x,"inline_data",None) and getattr(x.inline_data,"data",None))
   raw=OUTPUT/f"source_{i:02d}.wav"
   if audio.data[:4]==b"RIFF":raw.write_bytes(audio.data)
   else:
    m=re.search(r"rate=(\d+)",audio.mime_type or "")
    sr=int(m.group(1)) if m else 24000
    with wave.open(str(raw),"wb") as w:
     w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(audio.data)
   with wave.open(str(raw)) as w: duration=w.getnframes()/w.getframerate()
   if duration<1 or duration>75:raise RuntimeError(f"Unexpected duration {duration}")
   segs,info=model.transcribe(str(raw),language="ko",word_timestamps=True,beam_size=3,
                       condition_on_previous_text=False,vad_filter=False)
   transcript=[];word_times=[]
   for seg in segs:
    transcript.append(seg.text.strip())
    for word in seg.words or []:word_times.append({"text":word.word,"start":round(word.start,3),"end":round(word.end,3)})
   heard=" ".join(transcript)
   score=difflib.SequenceMatcher(None,cn(t),cn(heard),autojunk=False).ratio()
   # Strong guard against recording an unrelated hallucination or a cut-off passage.
   last=cn(t[-14:]); actual=cn(heard)
   print("ASR",i,"take",attempt+1,"sec",round(duration,2),"match",round(score,3),"words",len(word_times),"speech",heard[-180:],flush=True)
   if score<(.68 if r=="narrator" else .60) or len(actual)<len(cn(t))*.65:
    raise RuntimeError(f"ASR divergence {score:.2f}: {heard[-150:]}")
   # NO speeding up and NO trimming end syllables; add only 0.20 s silence per chunk.
   proc("ffmpeg","-hide_banner","-v","error","-y","-i",raw,
     "-af","loudnorm=I=-18:TP=-2:LRA=8,apad=pad_dur=0.20",
     "-ar","24000","-ac","1",dest)
   with wave.open(str(dest)) as w: length=w.getnframes()/w.getframerate()
   results.append({"index":i,**d,"voice":v,"file":dest.name,
       "duration":round(length,3),"source_duration":round(duration,3),"asr":heard,
       "asr_similarity":round(score,3),"word_times":word_times,"takes":attempt+1})
   print("ACCEPT",i,r,v,"length",round(length,2),"ASR",round(score,3),flush=True)
   # API tier-1 allows at most 10/min, generous spacing and retry.
   time.sleep(7)
   break
  except Exception as e:
   print("RETRY",i,attempt,str(e)[:320],flush=True)
   if attempt==5:raise
   time.sleep(15+attempt*15)
manifest={"title":"사람을 만날수록 더 외로워진 남자 - 민호","model":"gemini-2.5-flash-preview-tts",
 "speed":"original generated pace, no atempo or speedup","voices":voice,"chunks":results,
 "total_source_seconds":round(sum(z["duration"] for z in results),3),
 "text":"".join(x["text"] for x in results)}
(OUTPUT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf8")
assert len(results)==len(CHUNKS)
print("DONE",len(results),manifest["total_source_seconds"],flush=True)
