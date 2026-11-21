#!/usr/bin/env python3
"""Gemini Orus single continuous take for already approved Two Friends short.
Absolutely no per-line synthesis and no fallback voice.
"""
import os,re,wave,subprocess,json,time
from pathlib import Path
from google import genai
from google.genai import types

OUT=Path("two_friends_one_take_orus_output")
OUT.mkdir(parents=True,exist_ok=True)
LINES=[
"민수야… 나 네 밑에서 일하면 안 되겠냐?",
"대기업 부장 출신 준호가 삼십 년 지기 친구에게 꺼낸 말입니다.",
"가난했던 민수는 고등학교 졸업 후 곧바로 공사현장에 나갔습니다.",
"반면 준호는 대학 졸업 후 대기업에 입사했죠.",
"그때만 해도 민수는 준호가 부러웠습니다.",
"삼십 년 뒤, 민수는 배관과 용접을 익혀 자기 사업체를 운영했습니다.",
"반면 준호는 부장까지 오른 뒤 희망퇴직을 했습니다.",
"재취업은 번번이 실패했죠.",
"어느 날, 두 친구가 술잔을 기울였습니다.",
"민수야… 너희 회사에 사람 안 필요하냐?",
"자재 나르고, 청소하고, 허드렛일부터 할게.",
"월급 적어도 괜찮아. 나 진짜 다시 일하고 싶다.",
"너 부장까지 했잖아. 자존심 안 상하겠냐?",
"솔직히 상하지. 그런데 나만 바라보는 가족이 있잖아.",
"내 자존심보다 가족들 밥벌이가 먼저더라.",
"월요일부터 나와. 대신 처음부터 배워야 해.",
"가장의 용기는, 두려워도 가족을 위해 다시 시작하는 것입니다.",
"이 이야기가 마음에 남으셨다면 구독과 좋아요 부탁드립니다."
]
assert len(LINES)==18 and sum("구독과 좋아요" in x for x in LINES)==1
TEXT="\n".join(LINES)
(OUT/"approved_script.json").write_text(json.dumps({
    "voice":"Gemini Orus","voice_generation_count":1,"approach":"ONE uninterrupted TTS call",
    "script":LINES,"script_text":TEXT,"speed":1.12},ensure_ascii=False,indent=2),encoding="utf8")
prompt=(
    "You are ONE mature Korean male storyteller using voice Orus, reading a short life-story aloud. "
    "This is a SINGLE UNINTERRUPTED reading. Keep exactly the same speaker identity, timbre, accent, depth, pitch range, microphone distance, volume, and calm restrained emotional style throughout the complete story. "
    "Do NOT act the characters as different people; even quotations remain the same male narrator voice, just with a subtle earnest inflection. "
    "When the unemployed father asks for work, convey contained humility and determination, not melodramatic crying. "
    "Speak in natural standard Korean with short breath pauses at each sentence, but do not pause for long or speed up at the end. "
    "Read the complete text, word for word. Never add speech instructions, effects, music, intros, outro or repeated phrases. "
    "Read the final subscribe-and-like sentence exactly ONCE and finish the last syllable clearly. "
    "KOREAN SCRIPT TO READ VERBATIM:\n\n"+TEXT
)
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
audio=None
for attempt in range(4):
    try:
        response=client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Orus")))))
        for candidate in response.candidates:
            for part in candidate.content.parts:
                packet=getattr(part,"inline_data",None)
                if packet is not None and getattr(packet,"data",None):
                    audio=packet
                    break
            if audio:break
        if audio is None:raise RuntimeError("No audio returned")
        break
    except Exception as e:
        print("GEMINI_RETRY",attempt+1,str(e)[:300],flush=True)
        if attempt==3:raise
        time.sleep(5*(attempt+1))
raw=OUT/"two_friends_orus_one_take_raw.wav"
if audio.data.startswith(b"RIFF"):
    raw.write_bytes(audio.data)
else:
    m=re.search(r"rate=(\d+)",audio.mime_type or "")
    with wave.open(str(raw),"wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(int(m.group(1)) if m else 24000)
        f.writeframes(audio.data)
def run(*parts):
    subprocess.run(list(map(str,parts)),check=True)
out=OUT/"two_friends_orus_one_take.wav"
run("ffmpeg","-y","-hide_banner","-loglevel","error","-i",raw,
    "-af","atempo=1.12,loudnorm=I=-17:TP=-2:LRA=11",
    "-ar","24000","-ac","1","-sample_fmt","s16",out)
run("ffmpeg","-y","-hide_banner","-loglevel","error","-i",out,
    "-codec:a","libmp3lame","-b:a","160k",OUT/"two_friends_orus_one_take.mp3")
with wave.open(str(out),"rb") as f:
    duration=f.getnframes()/f.getframerate()
    peak_frames=f.getnframes()
assert 35<duration<130, f"Abnormal duration: {duration}"
report={"voice":"Google Gemini Orus","generation_mode":"ONE_CONTINUOUS_TAKE",
        "gemini_calls_successful":1,"segments_synthesized":1,
        "duration_seconds":round(duration,3),"playback_speed":1.12,
        "frames":peak_frames,"script_lines":len(LINES),
        "tail_speech_verification":"Requires ASR check; amplitude duration alone cannot prove every last word",
        "content_status":"Awaiting transcript verification"}
(OUT/"voice_qa.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
print("ONE_TAKE_COMPLETE",json.dumps(report,ensure_ascii=False),flush=True)
