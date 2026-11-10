"""Two source-grounded Korean 생활알고리즘 Shorts, single performance per topic.
Ref: VCA 'paw licking often caused by itchiness', Merck Interdigital Furunculosis;
EPA 'A Brief Guide to Mold' and CDC bathroom mold.
"""
from google import genai
from google.genai import types
from pathlib import Path
from io import BytesIO
import os, wave, re, json, time, traceback
O=Path("out_paw_bath_one_take");O.mkdir(exist_ok=True)
SCRIPTS={
"dog_paw":[
"강아지가 발을 계속 핥는다면? 단순한 습관이라고 넘기면 안 됩니다.",
"발바닥이나 발가락 사이가 가렵거나 아파서 핥는 경우가 많아요. 알레르기, 벌레 물림, 작은 상처나 이물질도 원인이 됩니다.",
"핥을수록 피부가 더 자극되고 세균이나 효모가 늘어 악순환이 생길 수도 있어요.",
"먼저 발가락 사이를 살펴보세요. 붉어짐, 냄새, 붓기, 진물이 있는지 확인하는 겁니다.",
"산책 후에는 묻은 먼지와 자극 물질을 깨끗한 젖은 천으로 닦고, 발가락 사이까지 잘 말려 주세요.",
"반복해서 소독하거나 사람용 연고를 임의로 바르는 건 피하세요. 원인에 따라 알레르기, 감염, 통증 치료가 달라집니다.",
"한쪽 발만 심하게 핥거나 절뚝거리고, 붓거나 피가 난다면 빨리 동물병원에 가세요.",
"우리 강아지 발 건강, 오늘부터 살펴보세요. 생활알고리즘, 구독과 좋아요!"
],
"bathroom":[
"샤워 후 욕실 문, 열어둘까요? 닫아둘까요? 정답은 문 하나에 있지 않습니다.",
"곰팡이가 좋아하는 건 오래 남아 있는 습기예요. 문을 닫은 채 환기도 안 하면 물기가 늦게 마릅니다.",
"그렇다고 문을 활짝 여는 것만으로 끝나는 것도 아닙니다. 습한 공기가 집 안으로 퍼질 수 있거든요.",
"가장 중요한 건 환풍기나 창문으로 습기를 바깥으로 내보내는 겁니다.",
"샤워하는 동안부터 환풍기를 켜고, 끝난 뒤에도 욕실이 충분히 마를 때까지 돌려 주세요. 필요하다면 문을 조금 열어 공기가 들어오게 합니다.",
"환풍기가 없으면 바깥 공기가 습하지 않을 때 창문을 활용하세요. 젖은 유리와 바닥은 물기를 닦아주면 더 빨리 마릅니다.",
"결론! 무조건 문을 열거나 닫는 것보다 욕실이 빨리 마르는 환기 방법을 찾는 게 핵심입니다.",
"곰팡이를 줄이는 생활 습관! 생활알고리즘 구독과 좋아요 부탁드립니다!"
]}
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
for key,lines in SCRIPTS.items():
 (O/(key+"_script.json")).write_text(json.dumps(lines,ensure_ascii=False,indent=2),encoding="utf-8")
 full="\n\n".join(lines)
 for attempt in range(3):
  try:
   response=client.models.generate_content(
    model="gemini-2.5-flash-preview-tts",
    contents="This is one continuous original Korean YouTube Short narration, spoken from first to last syllable by one consistent natural Charon Korean male voice; do not change voice/timbre or speakers; energetic opening 2 seconds then clear calm informative delivery, natural micro-pauses at each paragraph. No music, no added words, articulate every final word. Read the Korean content exactly:\n"+full,
    config=types.GenerateContentConfig(response_modalities=["AUDIO"],speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
   a=next(p.inline_data for p in response.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data)
   data=a.data; mime=a.mime_type or ""
   if data[:4]==b"RIFF":
    with wave.open(BytesIO(data),"rb") as r: rate=r.getframerate(); width=r.getsampwidth(); chans=r.getnchannels();data=r.readframes(r.getnframes())
   else:
    match=re.search(r"rate=(\d+)",mime);rate=int(match.group(1)) if match else 24000; width=2;chans=1
   with wave.open(str(O/(key+"_charon_one_take.wav")),"wb") as w: w.setnchannels(chans);w.setsampwidth(width);w.setframerate(rate);w.writeframes(data)
   print("VOICE_SUCCESS",key,"seconds",round(len(data)/rate/width/chans,2),flush=True)
   break
  except Exception as e:
   print("RETRY",key,attempt,type(e).__name__,str(e)[:400],flush=True)
   if attempt==2:raise
   time.sleep(18*(attempt+1))
 time.sleep(15)
print("DONE BOTH",flush=True)
