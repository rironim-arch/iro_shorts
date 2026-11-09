"""Gemini Charon 1-speaker voice for original phone charging safety Short.
No audio substitutions, no uploads.
"""
from pathlib import Path
import os, re, wave, json, time
from io import BytesIO
from google import genai
from google.genai import types

P=Path("out_phone_charon"); P.mkdir(exist_ok=True)
S=[
"휴대폰 충전하면서 베개 옆에 두고 자나요? 전자파가 걱정돼서요? 사실 더 조심할 게 있습니다.",
"휴대폰은 통신할 때 전자파를 내지만, 일반적인 사용으로 인한 건강 피해가 입증된 건 아닙니다. 연구는 계속되고 있어요.",
"그런데 충전 중 생기는 열은 다릅니다. 휴대폰을 베개 밑이나 이불 속에 두면 열이 제대로 빠져나가지 못해요.",
"그렇게 열이 갇히면 기기가 과열되고, 손상이나 화재 위험이 커질 수 있습니다. 잠들기 전에 충전 위치를 확인하세요.",
"충전할 땐 침구가 아닌, 통풍되는 협탁 위에 두세요. 케이블이 벗겨지거나 손상됐다면 교체하는 게 안전합니다.",
"전자파 걱정보다 먼저, 충전 습관부터 바꿔보세요! 도움이 됐다면 구독과 좋아요, 생활알고리즘!"
]
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
done=[]
for i,s in enumerate(S):
  for attempt in range(4):
    try:
      res=client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=("Read this Korean narration VERBATIM in clear natural Korean male Charon voice. "
                  "Gently energetic news-style Shorts delivery. Say every word exactly; no extras or effects. "
                  "Natural mini-pauses, finish sentences fully: \n"+s),
        config=types.GenerateContentConfig(
          response_modalities=["AUDIO"],
          speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
      x=next(p.inline_data for p in res.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data)
      raw=x.data; mime=x.mime_type or ""
      if raw[:4]==b"RIFF":
        with wave.open(BytesIO(raw),"rb") as f: rate=f.getframerate(); raw=f.readframes(f.getnframes())
      else:
        mat=re.search(r"rate=(\d+)",mime); rate=int(mat.group(1)) if mat else 24000
      with wave.open(str(P/f"scene_{i:02d}.wav"),"wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(rate); f.writeframes(raw)
      done.append({"i":i,"seconds":len(raw)/(rate*2),"text":s})
      (P/"meta.json").write_text(json.dumps(done,ensure_ascii=False,indent=2),encoding="utf8")
      print("SAVED",i,round(done[-1]["seconds"],2),flush=True)
      break
    except Exception as e:
      print("RETRY",i,attempt,str(e)[:300],flush=True)
      if attempt==3: raise
      time.sleep(70)
  time.sleep(22)
(P/"script.txt").write_text("\n".join(S),encoding="utf8")
