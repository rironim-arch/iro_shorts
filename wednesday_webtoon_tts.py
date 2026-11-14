"""Render voices for 'Wednesday Night Secret' Korean webtoon story."""
from pathlib import Path
import os, re, wave, time, json, subprocess
from google import genai
from google.genai import types
import imageio_ffmpeg

D=Path("wednesday_story_voice");D.mkdir(exist_ok=True)
# Each group is recorded as one continuous take to keep the narrator's timbre consistent.
groups=[
 {"voice":"Kore","lines":[
 "남편이 매주 수요일 밤마다 사라졌습니다.",
 "벌써 여섯 달째였죠.",
 "어디 가냐고 물으면 늘 회사 일이라고만 했습니다.",
 "그 시간엔 전화도 받지 않았어요.",
 "혹시 다른 여자가 생긴 건 아닐까요?",
 ]},
 {"voice":"Kore","lines":[
 "결국 어느 수요일, 저는 남편의 뒤를 밟았습니다.",
 "남편이 들어간 곳은 낯선 건물의 작은 교실.",
 "문틈으로 보니 여자들도 여럿 앉아 있었습니다.",
 "심장이 쿵 내려앉았습니다.",
 "그런데 이상했습니다. 아무도 말을 하지 않았어요.",
 "모두 두 손을 움직이며 이야기하고 있었죠.",
 "문에는 수어 교실이라고 적혀 있었습니다.",
 ]},
 {"voice":"Kore","lines":[
 "그날 밤, 저는 남편에게 이유를 물었습니다.",
 ]},
 {"voice":"Orus","lines":[
 "장모님이 청력을 잃으신 뒤로 식사 시간에 늘 혼자 계셨잖아.",
 "나도 어머니와 직접 이야기하고 싶었어.",
 ]},
 {"voice":"Kore","lines":[
 "며칠 뒤, 엄마의 생신날.",
 "남편이 엄마 앞에서 천천히 두 손을 움직였습니다.",
 ]},
 {"voice":"Orus","lines":[
 "어머니, 우리 가족이 되어 주셔서 감사합니다.",
 ]},
 {"voice":"Kore","lines":[
 "엄마는 남편의 손을 꼭 잡고 울기 시작했습니다.",
 "저도 고개를 들 수 없었습니다.",
 "제가 의심했던 여섯 달 동안 남편은 사랑을 전할 언어를 배우고 있었으니까요.",
 "이 내용이 마음에 드셨으면 구독과 좋아요 해주세요.",
 ]}
]
assert sum(s.count("구독과 좋아요") for g in groups for s in g["lines"]) == 1
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
ff=imageio_ffmpeg.get_ffmpeg_exe()
result=[]
for i,g in enumerate(groups):
 voice=g["voice"]
 script="\n".join(g["lines"])
 acting = ("You are a Korean female voice actor, a sincere and restrained first-person storyteller who starts suspicious and ends touched."
            if voice=="Kore" else
           "You are a Korean adult male voice actor playing a quiet, gentle, humble husband speaking to his wife or his mother-in-law.")
 prompt=acting+(" Use the exact same consistent Kore timbre on every Korean female group." if voice=="Kore" else
                 " Use the exact same consistent Orus timbre on every Korean male group.")
 prompt+=(" Read precisely the Korean lines below with natural short pauses at line breaks. "
           "Narrate with understated genuine emotion, clear natural standard Korean, no music, no effects, no extras, "
           "no greetings, no repeated sentences, no narration of instructions. "
           "Read subscription and like line at the very end once if present.\n\n"+script)
 raw=D/f"raw{i:02d}.wav"
 for attempt in range(5):
  try:
   r=client.models.generate_content(model="gemini-2.5-flash-preview-tts",contents=prompt,
      config=types.GenerateContentConfig(response_modalities=["AUDIO"],speech_config=types.SpeechConfig(
       voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)))))
   p=next(k.inline_data for k in r.candidates[0].content.parts if getattr(k,"inline_data",None) and k.inline_data.data)
   if p.data.startswith(b"RIFF"):raw.write_bytes(p.data)
   else:
    m=re.search(r"rate=(\d+)",p.mime_type or "")
    with wave.open(str(raw),"wb") as w:
     w.setnchannels(1);w.setsampwidth(2);w.setframerate(int(m.group(1)) if m else 24000);w.writeframes(p.data)
   break
  except Exception as e:
   print("RETRY",i,attempt,str(e)[:250],flush=True)
   if attempt==4:raise
   time.sleep(8*(attempt+1))
 target=D/f"part_{i:02d}_{voice.lower()}_125.wav"
 subprocess.run([ff,"-y","-loglevel","error","-i",str(raw),"-af","atempo=1.25","-ar","24000","-ac","1",str(target)],check=True)
 with wave.open(str(target),"rb") as w:duration=w.getnframes()/w.getframerate()
 raw.unlink()
 if duration<1.0:raise ValueError("Audio segment too short")
 result.append({"index":i,"voice":voice,"lines":g["lines"],"file":target.name,"duration":round(duration,3)})
 print("SEGMENT_READY",i,voice,duration,flush=True)
(D/"manifest.json").write_text(json.dumps({"segments":result,"duration":sum(x["duration"] for x in result)},ensure_ascii=False,indent=2),encoding="utf8")
print("VOICE_ALL_READY",sum(x["duration"] for x in result),flush=True)
