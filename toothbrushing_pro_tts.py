"""Try higher-quality Gemini Pro TTS once for remaining original dental Shorts narration.
No automatic publishing.
"""
import os,wave,re,sys
from pathlib import Path
from google import genai
from google.genai import types
p=Path("out_tooth_pro"); p.mkdir(exist_ok=True)
sections=[
 "그리고 의외의 포인트! 양치 후 치약은 뱉되, 곧바로 물로 여러 번 헹구지 않는 편이 불소 보호에 유리합니다.",
 "칫솔이 닿지 않는 치아 사이는 치실이나 치간칫솔로 하루 한 번 닦아주세요.",
 "오늘부터 바꿔보세요! 도움이 됐다면 좋아요와 구독! 생활알고리즘, 알아두면 쓸모 있는 생활상식."
]
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
for index,s in enumerate(sections,4):
 print("START",index,flush=True)
 try:
  r=client.models.generate_content(model="gemini-2.5-pro-preview-tts",contents="Read the next Korean educational YouTube Shorts narration verbatim in a warm and clear male voice, Charon. Normal conversational pace, fully pronounce each Korean ending without slurring or skipping, do not add any other speech:\n"+s,config=types.GenerateContentConfig(response_modalities=["AUDIO"],speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
  dd=next(v.inline_data for v in r.candidates[0].content.parts if getattr(v,"inline_data",None))
  rate=int(re.search("rate=(\\d+)",dd.mime_type).group(1)) if dd.mime_type and re.search("rate=(\\d+)",dd.mime_type) else 24000
  with wave.open(str(p/f"scene_{index:02}.wav"),"wb") as f:
   f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes(dd.data)
  print("SAVED",index,flush=True)
 except Exception as ex:
  print("TTS ERROR",index,str(ex)[:500],flush=True)
  sys.exit(1)
