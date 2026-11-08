"""생활알고리즘: 먹다 남은 치킨, Gemini Charon 한국어 음성 생성용.
YouTube 게시 없음. GitHub Actions에서만 사용.
"""
import os, re, wave, json, subprocess
from pathlib import Path
from google import genai
from google.genai import types

OUT = Path("output_chicken")
OUT.mkdir(parents=True, exist_ok=True)
SENTENCES = [
    "먹다 남은 치킨, 며칠까지 먹어도 될까요?",
    "어제 먹다 남은 치킨, 그냥 데워 먹어도 괜찮을까요?",
    "미국 농무부 USDA와 CDC 식품안전 지침에 따르면, 먹다 남은 치킨은 4도 이하 냉장고에서 3일에서 4일 이내에 먹는 것이 권장됩니다.",
    "하지만 중요한 건 냉장고에 넣기 전입니다. 일반적인 실내에서는 2시간 이내에 냉장 보관하세요.",
    "주변 온도가 32도를 넘는 더운 환경에서는 1시간 이내에 냉장고에 넣어야 합니다.",
    "겨울이라도 난방된 실내라면 예외가 아닙니다.",
    "전자레인지로 데울 때는 중간에 한 번 뒤집고, 치킨 속까지 74도 이상 가열하세요.",
    "실온에 오래 방치한 치킨은 다시 데운다고 안전해지는 것이 아닙니다.",
    "도움이 됐다면 구독과 좋아요! 생활알고리즘, 알아두면 쓸모 있는 생활상식!",
]
SCRIPT = " ".join(SENTENCES)
(OUT/"narration_script.txt").write_text(SCRIPT + "\n",encoding="utf-8")
key=os.environ.get("GEMINI_API_KEY")
if not key:
    raise RuntimeError("GEMINI_API_KEY secret is missing (do not put the secret in source code).")
client=genai.Client(api_key=key)
result=client.models.generate_content(
    model="gemini-2.5-flash-preview-tts",
    contents="Read the following Korean YouTube Shorts voiceover in a warm, crisp, engaging Korean male voice. Speak naturally at a steady conversational pace. Do not omit or add words. Text:\n\n"+SCRIPT,
    config=types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")
            )
        )
    )
)
parts=getattr(result.candidates[0].content,"parts",[]) if result.candidates else []
data=[p.inline_data for p in parts if getattr(p,"inline_data",None)]
if not data or not data[0].data:
    raise RuntimeError("Gemini did not return audio; check the model and API quota.")
voice=data[0]
raw=voice.data
mime=(voice.mime_type or "").lower()
out=OUT/"chicken_charon.wav"
if raw[:4] == b"RIFF" or "wav" in mime:
    out.write_bytes(raw)
else:
    if "pcm" not in mime and "audio/l16" not in mime and mime:
        raise RuntimeError("Unexpected Gemini TTS MIME: "+mime)
    rate_match=re.search(r"rate=(\d+)",mime)
    rate=int(rate_match.group(1)) if rate_match else 24000
    with wave.open(str(out),"wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(rate); wf.writeframes(raw)
subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(out),"-c:a","libmp3lame","-q:a","3",str(OUT/"chicken_charon.mp3")],check=True)
duration=subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(out)],text=True).strip()
(OUT/"info.json").write_text(json.dumps({"voice":"Gemini Charon","duration_seconds":float(duration),"status":"REVIEW_ONLY","youtube_upload":False},ensure_ascii=False,indent=2),encoding="utf-8")
print("Gemini Charon voice created, duration:",duration)
