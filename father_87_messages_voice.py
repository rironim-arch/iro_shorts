#!/usr/bin/env python3
import asyncio, json, subprocess, os, re, time
from pathlib import Path
import edge_tts

OUT=Path("father_87_output"); OUT.mkdir(exist_ok=True)
SCRIPT=[
"아버지, 바쁘니까 연락 좀 그만하세요.",
"아들은 매일 안부를 묻는 아버지가 귀찮았습니다.",
"밥은 먹었니? 비 오는데 우산은 챙겼고?",
"그날 이후, 아들은 석 달 동안 연락하지 않았습니다.",
"그러던 어느 날, 아버지가 병원에 입원했다는 연락을 받았습니다.",
"병실에서 아버지의 휴대폰을 켜자, 메모장에 제목 하나가 보였습니다.",
"보내지 못한 문자, 여든일곱 개.",
"생일 축하한다. 바쁠까 봐 전화는 안 했다.",
"비 온다는데, 감기 조심하고.",
"우리 아들이 바쁜 건, 잘 살고 있다는 뜻이겠지.",
"아들은 아버지 손을 꼭 잡고 울었습니다.",
"아버지, 저 오늘은 안 바빠요.",
"그러자 아버지가 미소 지으며 말했습니다.",
"그럼 우리 아들, 같이 밥 먹자.",
"사랑하는 사람에게 연락할 수 있는 오늘을 놓치지 마세요.",
"마음에 남았다면 구독과 좋아요 부탁드립니다."
]
content="\n".join(SCRIPT)
(OUT/"narration_script.txt").write_text(content,encoding="utf8")
async def main():
    # One continuous TTS take, never switch characters/voices mid-narration.
    tts=edge_tts.Communicate(content,voice="ko-KR-InJoonNeural",rate="+0%",volume="+0%")
    await tts.save(str(OUT/"original.mp3"))
asyncio.run(main())
subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(OUT/"original.mp3"),
                "-af","atempo=1.25,highpass=f=75,lowpass=f=11000",
                "-ar","24000","-ac","1",str(OUT/"father87_125.wav")],check=True)
subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(OUT/"father87_125.wav"),
                "-c:a","libmp3lame","-b:a","160k",str(OUT/"father87_125.mp3")],check=True)
import wave
with wave.open(str(OUT/"father87_125.wav"),"rb") as w:
    duration=w.getnframes()/w.getframerate()
print("SINGLE_VOICE_COMPLETE",{"duration":duration,"voice":"ko-KR-InJoonNeural","speed":1.25},flush=True)
# Recognized speech timings for actual caption sync, not guessed fractions.
from faster_whisper import WhisperModel
model=WhisperModel("small",device="cpu",compute_type="int8",cpu_threads=4)
segments,info=model.transcribe(str(OUT/"father87_125.wav"),language="ko",
    word_timestamps=True,vad_filter=False,beam_size=3,condition_on_previous_text=False)
words=[]
for seg in segments:
    for w in seg.words or []:
        if w.end>w.start and w.word.strip():
            words.append({"start":round(float(w.start),3),"end":round(float(w.end),3),"word":w.word.strip()})
if len(words)<35:raise RuntimeError(f"ASR word coverage too low {len(words)}")
(OUT/"words.json").write_text(json.dumps({"duration":duration,"words":words,"script":SCRIPT,
    "voice":"ko-KR-InJoonNeural","speed":1.25},ensure_ascii=False,indent=2),encoding="utf8")
print("WORD_ALIGNMENT",len(words),flush=True)
