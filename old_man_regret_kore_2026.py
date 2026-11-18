#!/usr/bin/env python3
import json, os, re, subprocess, wave, time
from pathlib import Path
from google import genai
from google.genai import types

out=Path("old_man_regret_kore_output")
out.mkdir(exist_ok=True)
chapters=[
"그는 평생 누구보다 열심히 살아온 사람이었습니다. 젊은 시절 사업을 일으켜 성공했고, 교회와 여러 모임에서도 활발히 활동했습니다. 어려운 이웃을 돕는 일에도 앞장섰죠. 사람들은 그를 존경했습니다.",
"그 역시 자신이 꽤 괜찮은 인생을 살아왔다고 믿었습니다. 하지만 가족들의 기억 속에 남은 그는 조금 다른 사람이었습니다. 집에서 그는 무척 엄격한 아버지였습니다.",
"그가 퇴근해 현관문을 열면, 떠들썩하던 집안이 조용해졌습니다. 아이들은 아버지의 눈치를 보았고, 아내는 남편의 기분이 상하지 않도록 늘 조심했습니다.",
"밥을 먹을 때도, 텔레비전을 볼 때도, 가족들은 그의 표정부터 살폈습니다. 자기 뜻대로 되지 않으면 그는 쉽게 화를 냈습니다. 내가 누구 때문에 이렇게 고생하는데! 부족한 것 없이 살게 해주면 됐지, 뭐가 불만이야!",
"밖에서는 남의 어려운 사정을 몇 시간이고 들어주면서, 정작 아내와 아이들의 이야기는 듣지 않았습니다. 그는 돈을 벌어오는 것이 가족을 사랑하는 방법이라 믿었습니다. 그러나 가족들에게 그 집은 편히 쉴 수 있는 곳이 아니었습니다.",
"그렇게 수십 년이 흘렀습니다. 아이들은 하나둘 독립했고, 아내마저 먼저 세상을 떠났습니다. 나이가 들어 몸이 약해진 그는 결국 요양원에서 지내게 되었습니다.",
"처음에는 자식들이 바빠서 찾아오지 못하는 줄 알았습니다. 하지만 생일이 지나고 명절이 지나도, 찾아오는 사람은 거의 없었습니다. 평생 받아온 감사패와 표창장은 여전히 그의 방에 놓여 있었습니다.",
"어느 날, 그는 오래된 가족사진을 꺼냈습니다. 문득 아내의 말이 떠올랐습니다. 당신은 밖에서는 그렇게 좋은 사람인데, 왜 집에서는 우리가 당신 눈치를 봐야 해요? 그때 이해하지 못했던 그 말이 이제야 가슴에 사무쳤습니다.",
"그는 가족에게 좋은 집과 생활비를 주었지만, 따뜻한 기억은 남겨주지 못했습니다. 가족을 책임진다는 이유로 그 마음을 외면했던 것입니다. 가족은 권위로 지키는 것이 아니라, 함께 있을 때 편안해야 곁에 남는다는 것을 이제야 깨달았습니다. 여러분은 가족에게 어떤 사람으로 기억되고 싶으신가요? 구독과 좋아요 부탁드립니다."
]
(out/"script.json").write_text(json.dumps({"title":"어느 늙은 노인의 후회","voice":"Kore","speed":1.25,"chapters":chapters},ensure_ascii=False,indent=2),encoding="utf8")
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
times=[]
for i,txt in enumerate(chapters):
 prompt=("다음 한국어 사연을 오직 여성 성우 Kore 한 명의 목소리로만 따뜻하지만 지나치게 감상적이지 않게 담담하게 읽어주세요. 오직 제공한 대본만 정확히 읽고, 효과음이나 음악, 원고에 없는 말은 금지합니다. 문장 사이에 자연스러운 아주 짧은 호흡을 두세요. 대사는 성대모사가 아닌 같은 여성 화자의 이야기 인용으로 읽으세요.\n\n"+txt)
 data=None
 for attempt in range(4):
  try:
   r=client.models.generate_content(model="gemini-2.5-flash-preview-tts", contents=prompt,
    config=types.GenerateContentConfig(response_modalities=["AUDIO"],speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")))))
   data=next((p.inline_data for p in r.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data),None)
   if data:break
  except Exception as ex:
   print("retry",i,attempt,str(ex)[:250],flush=True)
  time.sleep(8*(attempt+1))
 if data is None:raise RuntimeError("NO_AUDIO_DATA_"+str(i))
 raw=out/f"part_{i:02d}.wav"
 if data.data.startswith(b"RIFF"):raw.write_bytes(data.data)
 else:
  mime=data.mime_type or ""
  m=re.search(r"rate=(\d+)",mime)
  with wave.open(str(raw),"wb") as wf:
   wf.setnchannels(1);wf.setsampwidth(2);wf.setframerate(int(m.group(1)) if m else 24000);wf.writeframes(data.data)
 sped=out/f"part_{i:02d}_125.wav"
 subprocess.run(["ffmpeg","-y","-v","error","-i",str(raw),"-af","atempo=1.25,loudnorm=I=-17:TP=-2:LRA=11","-ar","24000","-ac","1",str(sped)],check=True)
 with wave.open(str(sped),"rb") as w: dur=w.getnframes()/w.getframerate()
 times.append({"chapter":i+1,"text":txt,"duration":round(dur,3)})
 print("SCENE",i+1,"DURATION",round(dur,2),flush=True)
 time.sleep(1)
lst=out/"concat.txt"
lst.write_text("\n".join("file 'part_%02d_125.wav'"%i for i in range(len(chapters)))+"\n",encoding="utf8")
subprocess.run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(lst),"-c:a","pcm_s16le",str(out/"old_man_regret_kore_125.wav")],check=True)
subprocess.run(["ffmpeg","-y","-v","error","-i",str(out/"old_man_regret_kore_125.wav"),"-b:a","128k",str(out/"old_man_regret_kore_125.mp3")],check=True)
(out/"timing.json").write_text(json.dumps({"scenes":times,"total_seconds":round(sum(x["duration"] for x in times),3)},ensure_ascii=False,indent=2),encoding="utf8")
print("ALL_READY",sum(x["duration"] for x in times),flush=True)
