import os,wave,time
from pathlib import Path
from google import genai
from google.genai import types
P=Path("out_tooth_tail");P.mkdir(exist_ok=True)
texts=[
"그리고 의외의 포인트! 양치 후 치약은 뱉되, 곧바로 물로 여러 번 헹구지 않는 편이 불소 보호에 유리합니다.",
"칫솔이 닿지 않는 치아 사이는 치실이나 치간칫솔로 하루 한 번 닦아주세요.",
"오늘부터 바꿔보세요! 도움이 됐다면 좋아요와 구독! 생활알고리즘, 알아두면 쓸모 있는 생활상식."
]
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
for i,s in enumerate(texts,4):
 r=client.models.generate_content(model="gemini-2.5-flash-preview-tts",contents="Read this Korean YouTube Short voiceover clearly and naturally, conversational male tone, medium pace, every word intact, no intro or added words: "+s,config=types.GenerateContentConfig(response_modalities=["AUDIO"],speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
 p=next(x.inline_data for x in r.candidates[0].content.parts if getattr(x,"inline_data",None))
 with wave.open(str(P/f"scene_{i:02}.wav"),"wb") as w:
  w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(p.data)
 print(i,len(p.data))
 time.sleep(2)
