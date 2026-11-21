#!/usr/bin/env python3
"""Mother's Savings Shorts: Gemini Kore voice, coherent multi-sentence takes."""
import os, json, re, time, wave, subprocess
from pathlib import Path
from google import genai
from google.genai import types
import imageio_ffmpeg
OUT=Path("mother_savings_voice_output"); OUT.mkdir(exist_ok=True)
LINES=[
"어릴 때 저는 엄마가 미웠습니다.",
"엄마는 돈을 정말 지독하게 아끼셨습니다.",
"친구들이 새 옷을 입을 때 저는 사촌 언니 옷을 물려받았죠.",
"용돈도 부족해서 떡볶이 하나 사 먹기 어려웠습니다.",
"엄마는 구멍 난 양말을 꿰매 신으시고,",
"마트에선 마감 할인 상품만 고르셨죠.",
"엄마, 우리는 왜 맨날 이렇게 살아야 해?",
"엄마는 늘 같은 말을 하셨습니다.",
"돈은 꼭 필요할 때 없으면 정말 서러운 거야.",
"저는 그 말이 지긋지긋했습니다.",
"세월이 흘러 결혼하고 아이도 낳았지만,",
"결국 이혼한 뒤 혼자 아이를 키우게 됐습니다.",
"전남편에게 받는 양육비는 월세와 생활비,",
"아이 교육비를 감당하기에 턱없이 부족했죠.",
"그런데 집주인이 보증금까지 올려 달라고 했습니다.",
"잠든 아이를 보며 한참을 울었습니다.",
"다음 날 엄마에게 사정을 털어놓자,",
"엄마는 낡은 통장 하나를 내미셨습니다.",
"이거 네가 써.",
"통장에 찍힌 돈을 보고 말문이 막혔습니다.",
"엄마, 이 돈을 어떻게 모았어?",
"엄마가 제 손을 꼭 잡으셨습니다.",
"어릴 때 남들처럼 못 해준 거, 엄마도 미안했어.",
"하지만 네가 힘든 날, 돈이 없어서 아이와 함께 갈 곳조차 없어지는 건 싫었어.",
"엄마의 낡은 신발과 꿰맨 양말이 떠올랐습니다.",
"그제야 알았습니다.",
"엄마가 평생 모은 건 단순한 돈이 아니라,",
"딸이 다시 일어설 수 있는 기회였다는 걸요.",
"이 이야기가 마음에 남으셨다면 구독과 좋아요 부탁드립니다."
]
CUTS=[0,10,20,len(LINES)]
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
ff=imageio_ffmpeg.get_ffmpeg_exe()
def run(a):subprocess.run(a,check=True)
manifest=[];pos=0.0
for ix,(st,en) in enumerate(zip(CUTS,CUTS[1:])):
 payload="\n".join(LINES[st:en])
 prompt=("다음은 한 명의 한국인 여성 성우가 처음부터 끝까지 동일한 목소리로 들려주는 따뜻하지만 담담한 인생 사연입니다. "
 "Kore 목소리로 일관된 적당히 감정을 담은 자연스러운 스토리텔링 톤을 유지하세요. "
 "원문의 모든 문장을 한 글자도 빠뜨리지 말고 순서대로, 문장 사이에는 0.2초 정도만 쉬면서 읽으세요. "
 "새로 말을 더하거나 목소리를 교체하거나 음악/효과음을 내지 마세요. "
 "마지막 글자까지 또렷하게 읽어 주세요.\n\n"+payload)
 data=None
 for attempt in range(4):
  try:
   response=client.models.generate_content(model="gemini-2.5-flash-preview-tts",contents=prompt,
    config=types.GenerateContentConfig(response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
      prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")))))
   for part in response.candidates[0].content.parts:
    d=getattr(part,"inline_data",None)
    if d is not None and getattr(d,"data",None):
     data=d;break
   if data:break
  except Exception as exc: print("RETRY",ix,attempt,str(exc)[:240],flush=True)
  time.sleep(3+attempt*3)
 if data is None:raise RuntimeError(f"TTS returned no audio for take {ix}")
 src=OUT/f"take_{ix:02d}_raw.wav"
 if data.data[:4]==b"RIFF":src.write_bytes(data.data)
 else:
  m=re.search(r"rate=(\d+)",data.mime_type or "")
  with wave.open(str(src),"wb") as w:
   w.setnchannels(1);w.setsampwidth(2);w.setframerate(int(m.group(1)) if m else 24000)
   w.writeframes(data.data)
 dest=OUT/f"take_{ix:02d}_125.wav"
 run([ff,"-hide_banner","-loglevel","error","-y","-i",str(src),"-af",
      "atempo=1.25,loudnorm=I=-17:TP=-2:LRA=8,adelay=150,apad=pad_dur=0.32",
      "-ar","24000","-ac","1","-sample_fmt","s16",str(dest)])
 with wave.open(str(dest),"rb") as w:
  dur=w.getnframes()/w.getframerate()
 if dur<5:raise RuntimeError(f"Take too short: {dur}")
 manifest.append({"take":ix,"start":round(pos,4),"end":round(pos+dur,4),
   "duration":round(dur,4),"line_start":st,"line_end":en,"lines":LINES[st:en]})
 pos+=dur
 print("TAKE",ix,"LINES",st,en,"DURATION",round(dur,2),"TOTAL",round(pos,2),flush=True)
(OUT/"concat.txt").write_text("\n".join("file 'take_%02d_125.wav'"%i for i in range(len(manifest)))+"\n",encoding="utf-8")
whole=OUT/"mother_savings_kore_125.wav"
run([ff,"-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(OUT/"concat.txt"),"-c:a","pcm_s16le",str(whole)])
run([ff,"-hide_banner","-loglevel","error","-y","-i",str(whole),"-b:a","160k",str(OUT/"mother_savings_kore_125.mp3")])
(OUT/"timing.json").write_text(json.dumps({"title":"엄마가 악착같이 돈을 모은 이유","voice":"Gemini Kore","speed":1.25,
 "duration":round(pos,4),"lines":LINES,"takes":manifest},ensure_ascii=False,indent=2),encoding="utf-8")
print("FINISHED total duration",round(pos,2),flush=True)
