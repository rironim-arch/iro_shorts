#!/usr/bin/env python3
"""Render from approved 18-frame reference layout and verified prior Gemini-Orus audio.
No new TTS service is called, and nothing is posted.
"""
import json,os,re,shutil,subprocess,urllib.request
from pathlib import Path
OUT=Path("two_friends_reference_final")
OUT.mkdir(exist_ok=True)
RUN=os.environ.get("VOICE_RUN_ID")
SRC=os.environ.get("REFERENCE_FRAMEPACK_URL")
if not RUN or not SRC or not SRC.startswith("https://"):raise RuntimeError("Expected existing TTS run and framepack")
subprocess.run(["gh","run","download",RUN,"-n","two-friends-orus-review-30fps","-D",str(OUT/"download")],check=True)
def find(name):
    matches=list((OUT/"download").rglob(name))
    if len(matches)!=1:raise RuntimeError(f"Missing or ambiguous artifact {name}: {matches}")
    return matches[0]
audio=find("gemini_orus_master.wav")
srt=find("two_friends_actual_tts.srt")
pack=OUT/"framepack.mp4"
urllib.request.urlretrieve(SRC,pack)
if pack.stat().st_size<100000:raise RuntimeError("Framepack damaged")
chunks=re.split(r"\n\s*\n",srt.read_text(encoding="utf8").strip())
assert len(chunks)==18,len(chunks)
def seconds(ts):
    h,m,sec=ts.replace(",",".").split(":")
    return 3600*int(h)+60*int(m)+float(sec)
starts=[];ends=[]
for entry in chunks:
    a=entry.splitlines()
    m=re.fullmatch(r"(\d\d:\d\d:\d\d,\d{3}) --> (\d\d:\d\d:\d\d,\d{3})",a[1])
    if not m:raise RuntimeError(f"Bad SRT time {a[1]}")
    starts.append(seconds(m.group(1)));ends.append(seconds(m.group(2)))
durs=[ends[i]-starts[i] for i in range(18)]
if any(d<0.8 for d in durs):raise RuntimeError("Unexpected short audio scene")
if any(abs(starts[i]-ends[i-1])>0.08 for i in range(1,18)):raise RuntimeError("Audio subtitle boundaries discontinuous")
for i,d in enumerate(durs):
    t=i*.35+.12
    subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error",
        "-ss",f"{t:.3f}","-i",str(pack),"-frames:v","1","-q:v","2",
        str(OUT/f"scene_{i:02}.jpg")],check=True)
txt=OUT/"video_concat.txt"
txt.write_text("".join(f"file 'scene_{i:02}.jpg'\nduration {d:.6f}\n" for i,d in enumerate(durs))
    +"file 'scene_17.jpg'\n",encoding="utf8")
def ffprobe(path):
    r=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
    "-of","default=noprint_wrappers=1:nokey=1",str(path)],check=True,capture_output=True,text=True)
    return float(r.stdout.strip())
mp4=OUT/"인생애니사연_30년만에뒤바뀐두친구_Orus_30fps.mp4"
subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error",
   "-f","concat","-safe","0","-i",str(txt),"-i",str(audio),
   "-map","0:v:0","-map","1:a:0","-vf","fps=30,format=yuv420p",
   "-c:v","libx264","-preset","veryfast","-crf","22",
   "-c:a","aac","-b:a","160k","-t",f"{ends[-1]:.3f}",
   "-movflags","+faststart",str(mp4)],check=True)
v=ffprobe(mp4);a=ffprobe(audio)
if abs(v-a)>0.6:raise RuntimeError(f"Duration mismatch: video={v}, audio={a}")
shutil.copy(srt,OUT/"실제Gemini음성기준자막.srt")
shutil.copy(audio,OUT/"Gemini_Orus_원본.wav")
metadata={"voice":"Gemini Orus from run "+RUN,"duration_seconds":round(v,3),
    "video_format":"1080x1920 30fps H.264/AAC","layout":"2026-11-21 user-provided reference screenshot header/title/subtitle coordinates",
    "subtitles":"1:1 per-line actual WAV durations, not guessed timing",
    "release_status":"UNPUBLISHED_REVIEW_REQUIRED"}
(OUT/"qa.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding="utf8")
print("FINAL_RENDER_COMPLETE",json.dumps(metadata,ensure_ascii=False),flush=True)
