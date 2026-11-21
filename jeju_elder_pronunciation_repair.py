#!/usr/bin/env python3
"""Re-record two ambiguous elder responses accurately; source clips are complete, no word slicing."""
import os,re,time,wave,subprocess,json
from pathlib import Path
from google import genai
from google.genai import types
from faster_whisper import WhisperModel
O=Path("jeju_decision_repair");O.mkdir(exist_ok=True)
LINES={9:"그래. 그땐 일 다 내려놓고 제주도에 꼭 가자.",13:"그래. 이번에는 제주도에 꼭 가자."}
cli=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
recognizer=WhisperModel("small",device="cpu",compute_type="int8",cpu_threads=4,num_workers=2)
def norm(x):return re.sub(r"[^가-힣]","",x)
reports=[]
for turn,script in LINES.items():
 good=False
 for attempt in range(5):
  voiceprompt=("당신은 칠십이 세 한국인 남성 성우입니다. Gemini Enceladus 목소리로 따뜻하고 자연스럽게 말하세요. "
   "평생 친구와 제주도 여행을 약속하는 순간이니 조용히 결심한 듯 밝게 말하세요. "
   "대본의 '제주도에 꼭 가자'가 중요한 말입니다. 가자가 하자로 바뀌지 않게 마지막 글자까지 정확하게 발음하세요. "
   "다른 말을 넣지 마세요. 대본: "+script)
  try:
   res=cli.models.generate_content(model="gemini-2.5-flash-preview-tts",contents=voiceprompt,
       config=types.GenerateContentConfig(response_modalities=["AUDIO"],speech_config=types.SpeechConfig(
       voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Enceladus")))))
   pk=next(p.inline_data for c in res.candidates for p in c.content.parts
           if getattr(p,"inline_data",None) and getattr(p.inline_data,"data",None))
   raw=O/f"turn_{turn}_raw.wav"
   if pk.data[:4]==b"RIFF":raw.write_bytes(pk.data)
   else:
    m=re.search(r"rate=(\d+)",pk.mime_type or "")
    with wave.open(str(raw),"wb") as w:
     w.setnchannels(1);w.setsampwidth(2);w.setframerate(int(m.group(1)) if m else 24000);w.writeframes(pk.data)
   wavfile=O/f"replacement_turn_{turn:02d}.wav"
   subprocess.run(["ffmpeg","-y","-v","error","-i",str(raw),"-af","loudnorm=I=-17:TP=-2:LRA=10",
      "-ar","24000","-ac","1",str(wavfile)],check=True)
   with wave.open(str(wavfile)) as w:duration=w.getnframes()/w.getframerate()
   if duration>20 or duration<2.2:raise RuntimeError("Abnormal duration")
   segs,_=recognizer.transcribe(str(wavfile),language="ko",beam_size=4,
       word_timestamps=True,condition_on_previous_text=False,vad_filter=False)
   segs=list(segs);spoken=" ".join(s.text.strip() for s in segs)
   print("FATHER_RETAKE_CHECK",turn,attempt,spoken,round(duration,2),flush=True)
   if "제주도" in norm(spoken) and "가자" in norm(spoken):
    reports.append({"turn":turn,"script":script,"recognized":spoken,"duration":duration,
                    "source":"Gemini Enceladus","complete":True})
    good=True;break
   raise RuntimeError("Critical final word '가자' missing in speech recognition")
  except Exception as e:
   print("RETRY_ELDER_LINE",turn,attempt,str(e)[:180],flush=True)
   if attempt<4:time.sleep(4)
 if not good:raise RuntimeError("Could not confirm full '가자' phrase for "+str(turn))
(O/"qa.json").write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding="utf8")
print("BOTH_ELDER_TRAVEL_PROMISES_COMPLETE",flush=True)
