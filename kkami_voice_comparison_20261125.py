from pathlib import Path
import os, wave, json, subprocess, time
from openai import OpenAI
p=Path("kkami_voice_comparison"); p.mkdir(exist_ok=True)
client=OpenAI(api_key=os.environ["OPENAI_API_KEY"],timeout=35,max_retries=1)
lines = [
("intro","까미야… 내가 널 지켜준 줄 알았는데, 평생 나를 지켜준 건 너였구나."),
("outro","마지막 꿈에서까지 나를 집에 데려다줘서 고마워. 우리… 언젠가 천국에서 꼭 다시 만나자.")
]
voices=["coral","nova","sage"]
style=("Narrate in natural Korean as an adult woman at the bedside of her beloved elderly dog after fifteen years together. "
       "The performance must sound like a real human talking to someone she loves, not a professional announcer, audiobook, ad, poem or newsreader. "
       "The first sentence comes softly as a sudden realization with vulnerability. "
       "A tiny unforced catch of breath before the last goodbye, a warm trembling low voice for '고마워', "
       "and a long tender sadness on '우리… 언젠가 천국에서 꼭 다시 만나자'. "
       "Do NOT overact, cry loudly, whisper inaudibly or sing. Clearly speak every Korean syllable. "
       "Maintain a gentle unhurried tempo, natural variation, small meaningful pauses. No music or sound effects.")
results=[]
for voice in voices:
    for part,txt in lines:
        key=f"{voice}_{part}"
        try:
            r=client.audio.speech.create(model="gpt-4o-mini-tts",voice=voice,input=txt,response_format="wav",speed=0.95,instructions=style)
            dest=p/f"{key}.wav";dest.write_bytes(r.content)
            print("VOICE_DONE",key,dest.stat().st_size,flush=True)
        except Exception as e:
            print("VOICE_FAILED",key,type(e).__name__,str(e)[:300],flush=True)
            raise
    flist=p/f"{voice}_concat.txt";flist.write_text(f"file '{voice}_intro.wav'\nfile '{voice}_outro.wav'\n",encoding="utf8")
    mp3=p/f"{voice}_까미_감정연기_비교.mp3"
    sub=subprocess.run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(flist),"-af","loudnorm=I=-17:TP=-1.5:LRA=11","-c:a","libmp3lame","-b:a","160k",str(mp3)],capture_output=True,text=True)
    if sub.returncode: raise RuntimeError(sub.stderr)
    duration=subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(mp3)],text=True).strip()
    results.append({"voice":voice,"file":mp3.name,"duration":duration,"size":mp3.stat().st_size})
    print("COMPLETE",voice,duration,flush=True)
(p/"comparison_manifest.json").write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding="utf8")
