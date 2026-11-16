#!/usr/bin/env python3
import os,re,subprocess,wave,json
from pathlib import Path
from google import genai
from google.genai import types

out=Path("father30_orus_output");out.mkdir(exist_ok=True)
script=[
"아버지, 바쁘니까 연락 좀 그만하세요.",
"그날 제가 아버지께 보낸 문자였습니다.",
"아버지는 매일 비슷한 안부를 물으셨습니다.",
"밥은 먹었니? 오늘 춥다. 따뜻하게 입어라.",
"저는 그게 귀찮은 잔소리인 줄만 알았습니다.",
"그날 이후 먼저 연락하지 않았고, 그렇게 석 달이 흘렀습니다.",
"어느 날 아버지가 병원에 입원하셨다는 연락을 받았습니다.",
"병실에서 아버지의 휴대폰을 정리하다 메모장 하나를 발견했습니다.",
"보내지 못한 문자, 서른 개.",
"생일 축하한다. 바쁠까 봐 전화는 안 했다.",
"비 온다는데 우산은 챙겼니?",
"마지막엔 이렇게 적혀 있었습니다.",
"우리 아들이 바쁜 건, 열심히 살고 있다는 뜻이겠지.",
"그제야 알았습니다.",
"제가 귀찮아하던 안부는, 아버지가 매일 저를 생각한 흔적이었다는 걸요.",
"저는 휴대폰을 내려놓고 말했습니다.",
"아버지, 앞으로는 제가 먼저 연락드릴게요.",
"아버지는 웃으며 물으셨습니다.",
"그래. 밥은 먹었고?",
"사랑은 때로 가장 평범한 말 속에 숨어 있습니다.",
"마음에 남으셨다면 구독과 좋아요 부탁드립니다."
]
text="\n".join(script)
(out/"script.json").write_text(json.dumps({"lines":script,"voice":"Orus","speed":1.25,"format":"9:16","topic":"보내지 못한 문자 30개"},ensure_ascii=False,indent=2),encoding="utf8")
prompt="다음 한국어 창작 사연을, 한 명의 한국 남성 전문 성우가 따뜻하고 자연스럽게 회상하듯 읽어주세요. Gemini Orus 목소리 하나만 처음부터 끝까지 유지하세요. 과장된 울음, 신파, 드라마 등장인물 흉내를 내지 마세요. 모든 인용 대사도 같은 Orus 한 명의 목소리로, 감정은 절제하고 문장만 자연스럽게 읽으세요. 읽는 내용에 없는 설명이나 효과음을 추가하지 마세요. 아래 원고만 그대로 읽으세요:\n\n"+text
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
try:
  r=client.models.generate_content(
    model="gemini-2.5-flash-preview-tts",
    contents=prompt,
    config=types.GenerateContentConfig(
       response_modalities=["AUDIO"],
       speech_config=types.SpeechConfig(
          voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Orus")
          )
       )
    )
  )
  pkt=next((p.inline_data for p in r.candidates[0].content.parts if getattr(p,'inline_data',None) and p.inline_data.data),None)
  if not pkt:raise RuntimeError("EMPTY_GEMINI_TTS")
  raw=out/"father30_orus_original.wav"
  if pkt.data.startswith(b"RIFF"):raw.write_bytes(pkt.data)
  else:
    rate=re.search(r"rate=(\d+)",pkt.mime_type or "")
    with wave.open(str(raw),"wb") as o:
      o.setnchannels(1);o.setsampwidth(2)
      o.setframerate(int(rate.group(1)) if rate else 24000)
      o.writeframes(pkt.data)
  fast=out/"father30_orus_125.wav"
  subprocess.run(["ffmpeg","-y","-v","error","-i",str(raw),"-af","atempo=1.25,loudnorm=I=-17:TP=-2:LRA=11","-ar","24000","-ac","1",str(fast)],check=True)
  subprocess.run(["ffmpeg","-y","-v","error","-i",str(fast),"-b:a","160k",str(out/"father30_orus_125.mp3")],check=True)
  with wave.open(str(fast),"rb") as w: duration=w.getnframes()/w.getframerate()
  if duration<25:raise RuntimeError("Voice too short, possible truncated TTS")
  print("VOICE_GENERATION_OK",json.dumps({"duration":round(duration,2),"voice":"Orus","speed":1.25,"sentences":len(script)}),flush=True)
except Exception as e:
  print("VOICE_FAILURE_DO_NOT_FALLBACK_TO_EDGE",str(e)[:700],flush=True)
  raise
