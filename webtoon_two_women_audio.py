"""Audio cues for the original female webtoon story Shorts; no paid video model."""
import os, json, re, wave, time, subprocess
from pathlib import Path
from google import genai
from google.genai import types
import imageio_ffmpeg

out=Path("webtoon_coworkers_audio")
out.mkdir(exist_ok=True)
segments=[
 {"voice":"Kore","lines":[
  "그 여자가 처음으로 제게 커피를 건넨 날, 저는 오히려 불안했습니다.",
  "그 여자는 3년 동안 같은 회사에서 저를 괴롭히던 선배였거든요.",
 ]},
 {"voice":"Kore","lines":[
  "입사 첫날부터 업무를 물어보면 한숨을 쉬었고,",
  "점심시간이면 저만 빼놓고 동료들과 식당에 갔습니다.",
 ]},
 {"voice":"Gacrux","lines":[
  "그런 것도 몰라요? 언제까지 가르쳐줘야 해요?",
 ]},
 {"voice":"Kore","lines":[
  "제가 밤새 준비한 자료를 자기 이름으로 보고한 적도 있었죠.",
  "그래도 참았습니다. 열심히 일하면 언젠가는 인정받을 거라고 생각했으니까요.",
  "그런데 어느 월요일 아침, 이상한 일이 벌어졌습니다.",
 ]},
 {"voice":"Gacrux","lines":[
  "커피 드실래요? 오늘 점심은 저랑 같이 먹어요.",
 ]},
 {"voice":"Kore","lines":[
  "늘 차갑던 사람이 갑자기 웃으며 다가왔습니다.",
  "처음엔 조금 기뻤습니다. 드디어 저를 동료로 인정해 주는 걸까요?",
  "하지만 다음 날, 그 이유를 알게 됐습니다.",
 ]},
 {"voice":"Kore","lines":[
  "제가 신설 부서의 팀장 후보로 추천됐다는 소식이 회사에 퍼진 겁니다.",
  "그 여자는 제가 자신의 상사가 될 수도 있다는 걸 이미 알고 있었던 거죠.",
  "그제야 깨달았습니다.",
 ]},
 {"voice":"Kore","lines":[
  "그 여자가 달라진 건 저를 보는 마음이 아니라, 제 위치를 바라보는 눈이었다는 걸요.",
  "사람의 진심은 필요할 때의 친절보다, 아무것도 바라지 않을 때의 태도에서 드러납니다.",
 ]},
 {"voice":"Kore","lines":[
  "이 내용이 마음에 드셨으면 구독과 좋아요 해주세요.",
 ]}
]
assert sum("\n".join(s["lines"]).count("구독과 좋아요") for s in segments)==1
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
ff=imageio_ffmpeg.get_ffmpeg_exe()
manifest=[]
for idx,segment in enumerate(segments):
    voice=segment["voice"]
    script="\n".join(segment["lines"])
    style=("A woman quietly telling a personal painful memory in a cinematic Korean drama. "
           "Her voice is intimate, natural, realistic and warm, not robotic or overacting."
           if voice=="Kore" else
           "A confident, slightly dismissive adult Korean female coworker speaking natural conversational Korean, "
           "and later politely when offering coffee. Do not exaggerate or sound like a villain.")
    prompt=("Speak the following Korean lines with the same consistent adult Korean female narrator voice throughout. "
            "Read exactly the lines in order and nothing more. Keep clear diction and brief natural line breaks, "
            "with no sound effects, no music, no additional commentary. "
            "Keep emotional consistency; one smooth continuous take for this section. "+
            style+"\nSCRIPT:\n"+script)
    raw=out/f"part_{idx:02d}_raw.wav"
    for attempt in range(5):
        try:
            result=client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)))))
            dat=next(p.inline_data for p in result.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data)
            if dat.data.startswith(b"RIFF"):
                raw.write_bytes(dat.data)
            else:
                sr=int(re.search(r"rate=(\d+)",dat.mime_type or "").group(1)) if re.search(r"rate=(\d+)",dat.mime_type or "") else 24000
                with wave.open(str(raw),"wb") as f:
                    f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr);f.writeframes(dat.data)
            break
        except Exception as e:
            print("RETRY",idx,attempt,str(e)[:220],flush=True)
            if attempt==4: raise
            time.sleep(10*(attempt+1))
    audio=out/f"part_{idx:02d}_{voice.lower()}_125.wav"
    subprocess.run([ff,"-y","-hide_banner","-loglevel","error","-i",str(raw),
                  "-af","atempo=1.25","-ar","24000","-ac","1",str(audio)],check=True,timeout=120)
    with wave.open(str(audio),"rb") as w:
        d=w.getnframes()/w.getframerate()
    if d < 1.0: raise RuntimeError("Unexpectedly short audio "+str(audio))
    raw.unlink()
    manifest.append({"index":idx,"voice":voice,"lines":segment["lines"],"audio":audio.name,"duration":round(d,3)})
    print("SEGMENT_READY",idx,voice,round(d,3),flush=True)
(out/"manifest.json").write_text(json.dumps({"segments":manifest,"speed":1.25,"credits":"Original fictional Korean workplace drama."},ensure_ascii=False,indent=2),encoding="utf-8")
print("COMPLETE_AUDIO",round(sum(x["duration"] for x in manifest),2),flush=True)
