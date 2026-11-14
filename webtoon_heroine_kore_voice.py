"""Render only the heroine's voice in three continuous takes, keeping Kore across narration and the final CTA.
The villain's 2 already verified Gacrux lines are re-used in the final editor.
"""
import os, re, wave, json, time, subprocess
from pathlib import Path
from google import genai
from google.genai import types
import imageio_ffmpeg
OUT=Path("webtoon_heroine_voice");OUT.mkdir(exist_ok=True)
BLOCKS=[
[
"그 여자가 처음으로 제게 커피를 건넨 날, 저는 오히려 불안했습니다.",
"그 여자는 3년 동안 같은 회사에서 저를 괴롭히던 선배였거든요.",
"입사 첫날부터 업무를 물어보면 한숨을 쉬었고,",
"점심시간이면 저만 빼놓고 동료들과 식당에 갔습니다.",
],
[
"제가 밤새 준비한 자료를 자기 이름으로 보고한 적도 있었죠.",
"그래도 참았습니다. 열심히 일하면 언젠가는 인정받을 거라고 생각했으니까요.",
"그런데 어느 월요일 아침, 이상한 일이 벌어졌습니다.",
],
[
"늘 차갑던 사람이 갑자기 웃으며 다가왔습니다.",
"처음엔 조금 기뻤습니다. 드디어 저를 동료로 인정해 주는 걸까요?",
"하지만 다음 날, 그 이유를 알게 됐습니다.",
"제가 신설 부서의 팀장 후보로 추천됐다는 소식이 회사에 퍼진 겁니다.",
"그 여자는 제가 자신의 상사가 될 수도 있다는 걸 이미 알고 있었던 거죠.",
"그제야 깨달았습니다.",
"그 여자가 달라진 건 저를 보는 마음이 아니라, 제 위치를 바라보는 눈이었다는 걸요.",
"사람의 진심은 필요할 때의 친절보다, 아무것도 바라지 않을 때의 태도에서 드러납니다.",
"이 내용이 마음에 드셨으면 구독과 좋아요 해주세요.",
]
]
assert sum(" ".join(s).count("구독과 좋아요") for s in BLOCKS)==1
cli=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
ff=imageio_ffmpeg.get_ffmpeg_exe()
metadata=[]
for index,lines in enumerate(BLOCKS):
    prompt=(
        "Produce Korean TTS spoken exclusively in the same SINGLE adult FEMALE voice called Kore, "
        "consistent gentle but confident sound in every section. "
        "This is the first-person thoughts and narration of an innocent female office worker. "
        "Never use the voice of the cruel female coworker, never act out other characters' direct dialogue. "
        "Speak precisely the supplied Korean sentences in their order, with short pauses between sentences. "
        "Keep a natural narrative pace, restrained emotion, articulate pronunciation. "
        "Never add greetings, never omit or repeat lines, and no music. "
        "The final 구독과 좋아요 is spoken exactly once as part of the same narrator's voice.\n\n"
        + "\n".join(lines)
    )
    raw=OUT/f"heroine_{index}_raw.wav"
    for attempt in range(4):
        try:
            res=cli.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")))))
            p=next(x.inline_data for x in res.candidates[0].content.parts if getattr(x,"inline_data",None) and x.inline_data.data)
            data=p.data
            if data.startswith(b"RIFF"):raw.write_bytes(data)
            else:
                match=re.search(r"rate=(\d+)",p.mime_type or "")
                sr=int(match.group(1)) if match else 24000
                with wave.open(str(raw),"wb") as w:
                    w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(data)
            break
        except Exception as ex:
            print("TTS_RETRY",index,attempt,str(ex)[:130],flush=True)
            if attempt==3:raise
            time.sleep(9*(attempt+1))
    outfile=OUT/f"heroine_kore_{index}_125.wav"
    subprocess.run([ff,"-y","-hide_banner","-loglevel","error","-i",str(raw),
        "-af","atempo=1.25","-ar","24000","-ac","1",str(outfile)],check=True)
    with wave.open(str(outfile),"rb") as w:
        duration=w.getnframes()/w.getframerate()
    if duration < 5:raise RuntimeError("Suspiciously short speech")
    print("HEROINE_KORE_READY",index,round(duration,2),flush=True)
    raw.unlink()
    metadata.append({"index":index,"voice":"Kore","audio":outfile.name,"lines":lines,"duration":round(duration,3)})
(OUT/"metadata.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding="utf8")
print("ALL_HEROINE_AUDIO_READY",flush=True)
