"""Audit all 11 existing Gemini TTS clips by independently transcribing the actual audio.
Don't trust the requested narration or onscreen text.
If duplicate CTA is found, output it clearly in the GitHub job logs.
"""
import os,json, re, time
from pathlib import Path
from google import genai
from google.genai import types

ROOT=Path("voice_audit")
ROOT.mkdir(exist_ok=True)
src=Path("voice")
data=json.loads((src/"manifest.json").read_text(encoding="utf-8"))["scenes"]
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
audits=[]
for i,x in enumerate(data):
    original=x["line"]
    filename=src/x["file"]
    request=[
        "이 한국어 오디오에 실제로 들리는 모든 말을 빠짐없이 그대로 받아쓰세요. "+
        "원래 대본을 추측하지 말고 실제 오디오만 듣고 받아쓰세요. "+
        "별도 설명, 의역, 화자 라벨을 추가하지 마세요. '구독', '좋아요' 등의 "+
        "광고성 문구가 들리면 반드시 그대로 포함하세요.",
        types.Part.from_bytes(data=filename.read_bytes(),mime_type="audio/wav")
    ]
    done=None
    for attempt in range(3):
        try:
            resp=client.models.generate_content(model="gemini-3.8-flash",contents=request)
            done=(resp.text or "").strip()
            if done:break
        except Exception as e:
            if attempt==2:raise
            time.sleep((attempt+1)*7)
    transcript=done or ""
    cta=bool(re.search(r"구\s*독|좋\s*아\s*요",transcript))
    expected_cta=i==len(data)-1
    result=dict(scene=i+1,expected=original,transcribed=transcript,has_cta=cta,
                expected_cta=expected_cta,unexpected_cta=(cta and not expected_cta))
    audits.append(result)
    print(f"SCENE {i+1}: CTA={'YES' if cta else 'NO'}",flush=True)
    print(f"ACTUAL TRANSCRIPT: {transcript}",flush=True)
(ROOT/"audit.json").write_text(json.dumps(audits,ensure_ascii=False,indent=2))
unexpected=[r["scene"] for r in audits[:-1] if r["unexpected_cta"]]
print("UNEXPECTED_CTA_SCENES:",unexpected,flush=True)
if unexpected:print("PROBLEM_CONFIRMED actual TTS narration inserted CTA",flush=True)
else:print("AUDIO_AUDIT_NO_UNEXPECTED_CTA",flush=True)
