#!/usr/bin/env python3
import os, re, wave, subprocess, json, time
from pathlib import Path
from google import genai
from google.genai import types
OUT=Path("super_owner_kore_output"); OUT.mkdir(exist_ok=True)
LINES=[
  "2000년대, 우리 동네에는 작은 슈퍼를 운영하던 여사장이 있었습니다.",
  "언제나 웃는 얼굴에 말솜씨도 좋고, 동네 사람들 사정까지 훤히 알고 있었죠.",
  "형편이 어려운 집에는 외상도 해주고, 누가 아프면 먼저 안부를 챙겼습니다.",
  "특히 동네 아줌마들 사이에서는 인기가 대단했습니다.",
  "그런데 그녀가 운영하던 건 슈퍼만이 아니었습니다.",
  "오래전부터 이웃들과 함께 계를 하고 있었거든요.",
  "처음에는 몇 사람이 적은 돈을 모았습니다.",
  "매달 돈을 내면 정해진 차례에 목돈을 받아 가는 방식이었죠.",
  "계돈도 약속한 날이면 꼬박꼬박 나왔습니다.",
  "그렇게 5년, 10년, 어느덧 15년이 넘었습니다.",
  "계를 들겠다는 사람이 늘어나며 오가는 돈도 커졌습니다.",
  "사람들은 말했습니다. 그 집 아줌마는 돈 하나는 확실해.",
  "누군가는 자식 결혼자금을, 누군가는 노후를 위해 모은 돈을 맡겼습니다.",
  "그러던 어느 날 아침, 슈퍼 셔터가 올라가지 않았습니다.",
  "처음에는 어디가 아픈 줄 알았죠.",
  "하지만 다음 날도, 그다음 날도 문은 굳게 닫혀 있었습니다.",
  "전화는 받지 않았고, 집도 텅 비어 있었습니다.",
  "그제야 동네에 믿기 힘든 소문이 퍼졌습니다.",
  "계주가 돈을 들고 한밤중에 도망갔다는 것이었습니다.",
  "당시 들은 이야기로는 그 돈이 무려 5억 원이 넘는다고 했습니다.",
  "15년 넘게 믿고 맡겼던 이웃들은 큰 충격을 받았습니다.",
  "그들이 잃은 건 돈뿐만이 아니었습니다.",
  "사람을 믿었던 마음까지 산산이 무너진 것이었죠.",
  "15년 동안 쌓아온 믿음이 무너지는 데는 단 하룻밤이면 충분했습니다.",
  "사람을 믿는 것과 돈을 맡기는 것은 다른 문제일지도 모릅니다.",
  "이 이야기가 마음에 남으셨다면 구독과 좋아요 부탁드립니다."
]
text="\n".join(LINES)
(OUT/"script.json").write_text(json.dumps({"voice":"Kore","script":LINES,"note":"Based on a remembered 2000s neighborhood story; amount 5억원 is unverified hearsay; creative dramatization.","target_seconds":"75-85","generation":"ONE uninterrupted voice take"},ensure_ascii=False,indent=2),encoding="utf-8")
prompt=(
 "당신은 한국어 여성 성우로, 오래전 동네의 가슴 아픈 사연을 담담하고 몰입감 있게 전하는 내레이션입니다. "
 "아래 전체 대본을 한국어로 단 한 번 처음부터 끝까지 읽으세요. "
 "목소리는 모든 문장에서 동일한 Gemini Kore 여성 음색과 같은 마이크 거리, 같은 음량, 같은 말속도입니다. "
 "대사 인용부도 다른 사람 목소리를 흉내 내지 말고 동일한 내레이션 목소리로만 읽으세요. "
 "앞부분은 정겹고 따뜻하게, 중간에는 조용히 긴장을 쌓고, 슈퍼가 닫힌 뒤부터 담담히 충격을 전하세요. "
 "중요한 결말을 앞에서 먼저 말하지 말고, 음성 원고에 없는 말이나 효과음, 음악은 절대 넣지 마세요. "
 "숫자 발음은 '5억 원'이고, 마지막 구독과 좋아요 문장은 맨 끝에서 딱 한 번만 읽으세요. "
 "말끝을 빠뜨리지 마세요. 문장 사이에 아주 짧은 호흡만 넣되 과한 쉼은 금지합니다.\n\n"
 + text)
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
last=None
for attempt in range(4):
 try:
  resp=client.models.generate_content(
   model="gemini-2.5-flash-preview-tts",contents=prompt,
   config=types.GenerateContentConfig(response_modalities=["AUDIO"],
      speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
         prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")))))
  pkt=next((p.inline_data for c in resp.candidates for p in c.content.parts
           if getattr(p,"inline_data",None) is not None and getattr(p.inline_data,"data",None)),None)
  if pkt is None:raise RuntimeError("Gemini returned empty audio")
  break
 except Exception as err:
  last=err
  print("TTS_RETRY",attempt,str(err)[:250],flush=True)
  if attempt==3:raise
  time.sleep(10*(attempt+1))
raw=OUT/"one_take_raw.wav"
if pkt.data[:4]==b"RIFF":raw.write_bytes(pkt.data)
else:
 m=re.search(r"rate=(\d+)",pkt.mime_type or "")
 with wave.open(str(raw),"wb") as w:
  w.setnchannels(1);w.setsampwidth(2);w.setframerate(int(m.group(1)) if m else 24000);w.writeframes(pkt.data)
target=OUT/"gemini_kore_one_take.wav"
subprocess.run(["ffmpeg","-y","-v","error","-i",str(raw),"-af","atempo=1.12,loudnorm=I=-17:TP=-2:LRA=10","-ar","24000","-ac","1",str(target)],check=True)
subprocess.run(["ffmpeg","-y","-v","error","-i",str(target),"-b:a","160k",str(OUT/"gemini_kore_one_take.mp3")],check=True)
with wave.open(str(target),"rb") as w:dur=w.getnframes()/w.getframerate()
if not 45<dur<145:raise RuntimeError(f"Unexpected audio duration {dur}")
(OUT/"voice_info.json").write_text(json.dumps({"voice":"Gemini Kore","speed":1.12,"duration_seconds":dur,"source_tts_calls":1,"voices":1,"full_last_phrase_unchecked_until_ASR":True},ensure_ascii=False,indent=2),encoding="utf8")
print("COMPLETE_KORE_SINGLE_VOICE",dur,flush=True)
