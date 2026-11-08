"""Narration for original 생활알고리즘 Shorts: 올바른 칫솔질. 
Gemini Charon 2.5 Flash TTS, seven short paragraphs to preserve enunciation.
"""
from pathlib import Path
from google import genai
from google.genai import types
from io import BytesIO
import os,re,wave,json,time
OUT=Path("output_brushing")
OUT.mkdir(exist_ok=True)
TEXTS=[
    "칫솔질, 세게 문지르면 더 깨끗할까요? 사실 중요한 건 힘보다 방법입니다.",
    "미국치과의사협회 권고에 따르면, 부드러운 칫솔을 잇몸 경계에 약 45도로 대세요. 세게 누르지 마세요.",
    "칫솔은 짧고 부드럽게 앞뒤로 움직이고, 치아 바깥쪽과 안쪽, 씹는 면까지 모두 닦습니다.",
    "앞니 안쪽은 칫솔을 세워 위아래로 움직이세요. 불소치약으로 하루 두 번, 한 번에 약 2분입니다.",
    "그리고 의외의 포인트! 양치 후 치약은 뱉되, 곧바로 물로 여러 번 헹구지 않는 편이 불소 보호에 유리합니다.",
    "칫솔이 닿지 않는 치아 사이는 치실이나 치간칫솔로 하루 한 번 닦아주세요.",
    "오늘부터 바꿔보세요! 도움이 됐다면 좋아요와 구독! 생활알고리즘, 알아두면 쓸모 있는 생활상식."
]
key=os.getenv("GEMINI_API_KEY")
if not key: raise RuntimeError("Missing Gemini API key secret")
client=genai.Client(api_key=key)
metadata=[]
for i,text in enumerate(TEXTS):
    prompt=("Read the following Korean educational video narration word-for-word, in a friendly confident, clear Korean male voice, " 
            "moderate speed, preserve Korean syllables and sentence endings clearly, "
            "no words omitted or added, natural brief phrase pauses, no sound effects: \n\n"+text)
    response=client.models.generate_content(
      model="gemini-2.5-flash-preview-tts",
      contents=prompt,
      config=types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
           voice_config=types.VoiceConfig(
               prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")
           )
        )
      )
    )
    if not response.candidates: raise RuntimeError(f"No candidate for paragraph {i}")
    audio=[p.inline_data for p in response.candidates[0].content.parts if getattr(p,"inline_data",None)]
    if not audio or not audio[0].data: raise RuntimeError(f"No audio for paragraph {i}")
    raw=audio[0].data
    mime=(audio[0].mime_type or "").lower()
    if raw[:4]==b"RIFF" or "wav" in mime:
        with wave.open(BytesIO(raw),"rb") as wav:
            ch,rate,width=wav.getnchannels(),wav.getframerate(),wav.getsampwidth()
            frames=wav.readframes(wav.getnframes())
    elif not mime or "pcm" in mime or "audio/l16" in mime:
        m=re.search("rate=([0-9]+)",mime)
        rate=int(m.group(1)) if m else 24000
        ch,width,frames=1,2,raw
    else: raise RuntimeError("Unsupported audio type "+mime)
    assert ch==1 and width==2
    target=OUT/f"scene_{i:02d}.wav"
    with wave.open(str(target),"wb") as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes(frames)
    metadata.append({"index":i,"text":text,"duration":round(len(frames)/(rate*2),4),"sample_rate":rate})
    print(f"Generated {i+1}/{len(TEXTS)} voice scene ({metadata[-1]['duration']} s)",flush=True)
    if i<len(TEXTS)-1:time.sleep(2)
(OUT/"narration.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding="utf-8")
(OUT/"script.txt").write_text("\n".join(TEXTS),encoding="utf-8")
print("All Gemini Charon audio done.",flush=True)
