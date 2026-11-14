"""Two comparable voice auditions for the same original Korean webtoon script."""
import os, re, wave, time, json, subprocess
from pathlib import Path
from google import genai
from google.genai import types
import imageio_ffmpeg

OUT=Path("voice_comparison_samples")
OUT.mkdir(exist_ok=True)
FFMPEG=imageio_ffmpeg.get_ffmpeg_exe()
lines=[
"3년 동안 저를 무시하던 직장 동료가 있었습니다.",
"인사를 해도 못 들은 척. 회의에서는 제 말을 끊었죠.",
"그런데 어느 날, 그 사람이 웃으며 커피를 건넸습니다.",
"어제까지 눈도 마주치지 않던 사람이 말입니다.",
"왜 갑자기 친절해진 걸까요?",
"이유는 다음 날 알게 됐습니다.",
"제가 다른 부서의 팀장으로 승진한다는 소식이 퍼진 겁니다.",
"그제야 깨달았습니다.",
"달라진 건 그 사람의 마음이 아니라, 제 위치를 바라보는 눈이었죠.",
"이런 짧은 이야기가 좋다면, 구독과 좋아요."
]
text="\n".join(lines)
assert text.count("구독과 좋아요")==1
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def generate(name):
    prompt=(
        "You are a Korean audiobook-style male narrator. Read the exact text below as one continuous take. "
        "Speak with believable human emotion and articulate modern standard Korean. "
        "The mood is restrained, dramatic and quietly disappointed; a short workplace betrayal story. "
        "Keep natural pauses. Make the last line a friendly call to action, exactly once. "
        "Do not speak any words outside the script, do not improvise, do not repeat. No background music.\n\n"
        + text
    )
    raw=OUT/f"{name.lower()}_raw.wav"
    for attempt in range(4):
        try:
            res=client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=name)))))
            part=next(p.inline_data for p in res.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data)
            dat=part.data
            if dat.startswith(b"RIFF"):raw.write_bytes(dat)
            else:
                match=re.search(r"rate=(\\d+)",part.mime_type or "")
                sr=int(match.group(1)) if match else 24000
                with wave.open(str(raw),"wb") as w:
                    w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(dat)
            break
        except Exception as ex:
            print("RETRY",name,attempt,str(ex)[:200],flush=True)
            if attempt==3:raise
            time.sleep(8*(attempt+1))
    mp3=OUT/f"webtoon_story_{name.lower()}_125x.mp3"
    subprocess.run([FFMPEG,"-y","-hide_banner","-loglevel","error","-i",str(raw),
                    "-af","atempo=1.25","-ar","24000","-ac","1","-b:a","128k",str(mp3)],check=True,timeout=120)
    if mp3.stat().st_size<100_000:raise RuntimeError("Output unexpectedly small")
    print("VOICE_READY",name,"mp3_bytes",mp3.stat().st_size,flush=True)
    raw.unlink()
    return {"name":name,"filename":mp3.name,"bytes":mp3.stat().st_size}
info=[generate(n) for n in ["Algenib","Orus"]]
(OUT/"voice_comparison.json").write_text(json.dumps({"title":"3년간 나를 무시하던 동료가 갑자기 친절해진 이유","speed":"1.25x","lines":lines,"voices":info},ensure_ascii=False,indent=2),encoding="utf8")
print("ALL_READY",flush=True)
