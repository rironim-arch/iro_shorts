"""MeloTTS MIT Korean fallback for chapters 10-12 after Gemini free quota."""
import json,re,wave,os,subprocess
from pathlib import Path
from melo.api import TTS

data=json.loads(Path("senior_story_01.json").read_text(encoding="utf-8"))
folder=Path("melo_story_audio");folder.mkdir(exist_ok=True)
model=TTS(language="KR",device="cpu")
speakers=model.hps.data.spk2id
speaker=speakers["KR"]
print("available speakers",list(speakers.keys()),flush=True)

def split(t,limit=110):
    sentences=re.split(r'(?<=[.!?])\s+',t)
    parts=[];buf=""
    for s in sentences:
        if len(buf)+len(s)+1<=limit:buf=(buf+" "+s).strip();continue
        if buf:parts.append(buf);buf=""
        while len(s)>limit:
            ix=s.rfind(" ",0,limit)
            if ix<=20:ix=limit
            parts.append(s[:ix]);s=s[ix:].strip()
        buf=s
    if buf:parts.append(buf)
    return parts

for ch in data["chapters"][9:]:
    parts=split(ch["script"])
    temp=folder/f'temp_{ch["chapter"]:02}'
    temp.mkdir(exist_ok=True)
    wav_paths=[]
    for i,part in enumerate(parts):
        wav_path=temp/f'part_{i:03}.wav'
        model.tts_to_file(part,speaker,str(wav_path),speed=0.85)
        wav_paths.append(wav_path)
        print("chapter",ch["chapter"],"segment",i+1,"of",len(parts),flush=True)
    lst=temp/"parts.txt"
    lst.write_text("".join("file '"+p.name+"'\n" for p in wav_paths),encoding="utf-8")
    output=folder/f'chapter_{ch["chapter"]:02}.wav'
    subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error",
        "-f","concat","-safe","0","-i",str(lst),"-ar","24000","-ac","1","-c:a","pcm_s16le",str(output)],
        check=True,cwd=None)
    # Note ffmpeg concat file paths relative to list file location.
    with wave.open(str(output),"rb") as w:sec=w.getnframes()/w.getframerate()
    if sec<40: raise RuntimeError(f"Unexpectedly short TTS chapter {ch['chapter']} duration {sec:.1f}")
    print("DONE chapter",ch["chapter"],"seconds",sec,flush=True)
print("All final 3 chapters generated with MeloTTS",flush=True)
