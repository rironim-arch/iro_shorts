"""One-off narration for an original long Korean senior drama; outputs 12 WAV parts."""
import os, json, wave, re, time, sys, traceback
from pathlib import Path
from google import genai
from google.genai import types

data=json.loads(Path("senior_story_01.json").read_text(encoding="utf-8"))
out=Path("senior_audio")
out.mkdir(exist_ok=True)
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL="gemini-2.5-flash-preview-tts"
FAILED=[]
def synth(chapter_number, text):
    voice=types.SpeechConfig(voice_config=types.VoiceConfig(
        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")))
    instructions=(
        "Perform a Korean first-person narrative audiobook from the perspective of a 70-year-old "
        "Korean grandmother. Female Korean voice, warm and mature, heartfelt but dignified. "
        "Speak slowly and clearly for elderly listeners, about 0.85 times normal pace. "
        "Naturally distinguish quoted dialogue from narration with emotional intonation, "
        "but keep ONE consistent speaker. Read every word accurately, no omissions or additions."
        "\n\n" + text
    )
    res=client.models.generate_content(
        model=MODEL,contents=instructions,
        config=types.GenerateContentConfig(response_modalities=["AUDIO"],speech_config=voice))
    if not res.candidates: raise RuntimeError("No response candidates")
    aud=next((p.inline_data for p in res.candidates[0].content.parts if getattr(p,"inline_data",None)),None)
    if not aud or not aud.data: raise RuntimeError("No audio data")
    raw=aud.data
    mime=(aud.mime_type or "").lower()
    path=out/f"chapter_{chapter_number:02}.wav"
    if "wav" in mime or raw[:4]==b"RIFF":
        path.write_bytes(raw)
    elif "pcm" in mime or "l16" in mime or not mime:
        m=re.search(r"rate=(\d+)",mime)
        rate=int(m.group(1)) if m else 24000
        with wave.open(str(path),"wb") as wav:
            wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(rate);wav.writeframes(raw)
    else: raise RuntimeError("Unknown output audio format "+mime)
    with wave.open(str(path),"rb") as w:
        sec=w.getnframes()/w.getframerate()
    print(f"Chapter {chapter_number} duration {sec:.1f}s audio size {path.stat().st_size}",flush=True)
    if sec<30:
        raise RuntimeError("Generated narration suspiciously short: "+str(sec))
    return sec

for ch in data["chapters"]:
    i=ch["chapter"]
    success=False
    for attempt in range(3):
        try:
            synth(i,ch["script"])
            success=True
            break
        except Exception as e:
            print(f"chapter {i} attempt {attempt+1} failure: {type(e).__name__}: {str(e)[:240]}",flush=True)
            if attempt<2: time.sleep(25*(attempt+1))
    if not success:
        FAILED.append(i)
    time.sleep(3)

report={"total":len(data["chapters"]),"failed":FAILED,
        "finished":[i for i in range(1,len(data["chapters"])+1) if i not in FAILED]}
(out/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print("RESULT",report,flush=True)
if FAILED: sys.exit(1)
