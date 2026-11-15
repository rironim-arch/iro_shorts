#!/usr/bin/env python3
"""Cut and pan across 48 original illustrated story frames; original Gemini Kore subtitles."""
import os, math, json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
AUDIO=ROOT/"somin_v2_audio_output"
ART=ROOT/"somin_v2_art"
OUT=ROOT/"somin_v2_release";OUT.mkdir(exist_ok=True)
PLAN=json.loads((ROOT/"somin_v2_scene_plan.json").read_text(encoding="utf8"))
QA=json.loads((AUDIO/"somin_v2_speech_alignment_QA.json").read_text(encoding="utf8"))
seconds=QA["chapters"]
durations=[float(seconds[str(i)]) for i in range(1,9)]
frames=15
clips=[]
# each shot corresponds to an actual change of place, character emotion, and story beat.
for c in PLAN["chapters"]:
    chapter=c["number"]
    d=durations[chapter-1]/len(c["shots"])
    for s in c["shots"]:
        src=ART/f"scene_{chapter:02}_{s['index']:02}.jpg"
        if not src.exists() or src.stat().st_size<10000:
            raise RuntimeError(f"Missing essential story illustration: {src}")
        dst=OUT/f"shot_{chapter:02}_{s['index']:02}.mp4"
        nf=int(round(d*frames))
        # Simulate careful camera operation on a genuine cinematic frame:
        # slow push / pan for each 30-55s story beat, no 1-second cuts, no text-card backgrounds.
        # Dynamic crop samples from enlarged illustration; the context and people remain visible.
        x=f"(in_w-out_w)*(0.50+0.22*sin(n/240+{s['index']}))"
        y=f"(in_h-out_h)*(0.50+0.19*cos(n/290+{chapter}))"
        vf=f"scale=2304:1296:flags=lanczos,crop=1920:1080:x='{x}':y='{y}',format=yuv420p"
        cmd=["ffmpeg","-y","-hide_banner","-loglevel","error",
             "-loop","1","-framerate",str(frames),"-i",str(src),
             "-vf",vf,"-frames:v",str(nf),
             "-c:v","libx264","-preset","veryfast","-crf","25",
             "-pix_fmt","yuv420p","-an",str(dst)]
        if not dst.exists() or dst.stat().st_size<20000:
            subprocess.run(cmd,check=True,timeout=1200)
        clips.append(dst)
        print("CAMERA_SHOT_READY",chapter,s["index"],round(nf/frames,1),flush=True)
listfile=OUT/"sequence.txt"
with listfile.open("w",encoding="utf8") as fp:
    for clip in clips:
        fp.write("file '"+str(clip.resolve()).replace("'","'\\''")+"'\n")
full=OUT/"somin_v2_picture.mp4"
subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error",
    "-f","concat","-safe","0","-i",str(listfile),"-c","copy",str(full)],check=True,timeout=1200)
audio=AUDIO/"somin_narration.wav"
ass=AUDIO/"somin_v2.ass"
mp3=AUDIO/"somin_v2_kore125.mp3"
srt=AUDIO/"somin_v2.srt"
for f in [audio,ass,mp3,srt]:
    if not f.exists() or f.stat().st_size<100:raise RuntimeError(f"Missing voice/subtitle file {f}")
final=OUT/"somin_v2_cinematic_anime_full.mp4"
subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error",
    "-i",str(full),"-i",str(audio),"-map","0:v","-map","1:a",
    "-vf",f"ass={ass}",
    "-t",f"{QA['duration_seconds']:.3f}",
    "-c:v","libx264","-preset","veryfast","-crf","24",
    "-pix_fmt","yuv420p","-c:a","aac","-b:a","128k",
    "-movflags","+faststart",str(final)],check=True,timeout=6300)
if final.stat().st_size<10_000_000:raise RuntimeError("Final output abnormally small")
(OUT/"somin_v2.srt").write_bytes(srt.read_bytes())
(OUT/"somin_v2_kore125.mp3").write_bytes(mp3.read_bytes())
(OUT/"completion_report.json").write_text(json.dumps({
    "output_mp4":final.name,"bytes":final.stat().st_size,
    "duration_s":QA["duration_seconds"],"cinematic_illustrations":len(clips),
    "subtitles":QA["caption_count"],
    "voice":"Gemini 2.5 Flash TTS Kore single speaker at 1.25x",
    "caption_method":"ASR word alignment; text coverage checked per speech chunk",
    "style":"Original contextual Korean animation-film stills with gentle camera movement"
},ensure_ascii=False,indent=2),encoding="utf8")
print("SOMIN_V2_COMPLETED",final,final.stat().st_size,flush=True)
