import os,re,wave,subprocess,time
from pathlib import Path
from google import genai
from google.genai import types
O=Path("father_remarriage_cta");O.mkdir(exist_ok=True)
text="이 이야기가 마음에 남으셨다면 구독과 좋아요 부탁드립니다."
prompt="한국어 여성 성우 Kore. 차분하고 따뜻한 사연 내레이션의 마지막 문장입니다. 자연스러운 속도로 감정을 과장하지 말고 아래 문장을 정확히 한 번만, 마지막 '부탁드립니다'의 끝 음절까지 또렷하게 읽으세요. 음성 이외의 소리나 추가 문구는 금지합니다.\\n\\n"+text
c=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
for n in range(4):
 try:
  r=c.models.generate_content(model="gemini-2.5-flash-preview-tts",contents=prompt,config=types.GenerateContentConfig(response_modalities=["AUDIO"],speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")))))
  pk=next(p.inline_data for z in r.candidates for p in z.content.parts if getattr(p,"inline_data",None) and getattr(p.inline_data,"data",None))
  break
 except Exception as e:
  print("retry",n,str(e)[:150],flush=True)
  if n==3:raise
  time.sleep(6)
raw=O/"cta_raw.wav"
if pk.data.startswith(b"RIFF"):raw.write_bytes(pk.data)
else:
 m=re.search(r"rate=(\\d+)",pk.mime_type or "")
 with wave.open(str(raw),"wb") as w:
  w.setnchannels(1);w.setsampwidth(2);w.setframerate(int(m.group(1)) if m else 24000);w.writeframes(pk.data)
out=O/"cta_kore.wav"
subprocess.run(["ffmpeg","-y","-v","error","-i",str(raw),"-af","loudnorm=I=-17:TP=-2:LRA=10","-ar","24000","-ac","1",str(out)],check=True)
with wave.open(str(out)) as w:sec=w.getnframes()/w.getframerate()
if not 2<sec<16:raise RuntimeError(f"CTA duration unexpected: {sec}")
print("CTA_OK",sec)
