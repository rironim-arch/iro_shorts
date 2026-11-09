from pathlib import Path
from google import genai
from google.genai import types
from io import BytesIO
import os,re,wave,time,json
P=Path("out_down_jacket_charon");P.mkdir(exist_ok=True)
texts=[
"다운패딩, 무조건 드라이클리닝 맡기시나요? 사실 그게 정답은 아닙니다.",
"가장 먼저 안쪽 세탁 라벨을 확인하세요. 물세탁이 가능하다면 집에서도 관리할 수 있어요.",
"다운 전용 세제로 찬물에 부드럽게 세탁하세요. 드럼 세탁기가 권장되며, 섬유유연제와 표백제는 피하세요.",
"진짜 중요한 건 건조입니다. 건조기 사용이 허용됐다면 낮은 온도로 충분히 말리고, 뭉친 솜털을 풀어주세요.",
"다만 특수 소재나 장식이 있거나 물세탁 금지 표시가 있다면 제품 안내를 따르세요. 모든 패딩에 같은 방법을 쓰면 안 됩니다.",
"내 패딩의 세탁 라벨부터 확인! 도움이 됐다면 구독과 좋아요, 생활알고리즘."
]
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
done=[]
for i,s in enumerate(texts):
 for tries in range(4):
  try:
   r=client.models.generate_content(model="gemini-2.5-flash-preview-tts",
     contents="Read ONLY this Korean script verbatim. Confident friendly male educational narration, clear natural Korean, medium pace and distinct endings, do not add anything.\n"+s,
     config=types.GenerateContentConfig(response_modalities=["AUDIO"],speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
   x=next(p.inline_data for p in r.candidates[0].content.parts if getattr(p,"inline_data",None))
   raw=x.data; mime=x.mime_type or ""; hz=int(re.search(r"rate=(\d+)",mime).group(1)) if re.search(r"rate=(\d+)",mime) else 24000
   if raw[:4]==b"RIFF":
    with wave.open(BytesIO(raw),"rb") as f: hz=f.getframerate(); raw=f.readframes(f.getnframes())
   with wave.open(str(P/f"scene_{i:02}.wav"),"wb") as f:
    f.setnchannels(1);f.setsampwidth(2);f.setframerate(hz);f.writeframes(raw)
   done.append({"index":i,"text":s,"seconds":len(raw)/(hz*2)})
   (P/"report.json").write_text(json.dumps(done,ensure_ascii=False,indent=2),encoding="utf8")
   print("SAVED",i,done[-1]["seconds"],flush=True)
   break
  except Exception as e:
   print("ERROR",i,tries,str(e)[:400],flush=True)
   if tries==3: raise
   time.sleep(70)
 time.sleep(24)
