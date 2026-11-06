"""생활알고리즘 Adler 01: alternate Korean male narration through Edge TTS.
Creates review-only video, voice WAV and synchronized scene captions; no upload.
"""
import asyncio
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from adler_episode_01 import BEATS, OUT, draw_frame, run, duration, timestamp

VOICE = "ko-KR-HyunsuMultilingualNeural"
SPEED = 1.25

async def synthesize(text, dest):
    import edge_tts
    for attempt in range(3):
        try:
            com = edge_tts.Communicate(text, VOICE, rate="+0%")
            await com.save(str(dest))
            if dest.stat().st_size < 1500:
                raise RuntimeError("Edge voice output too small")
            return
        except Exception as exc:
            if attempt == 2:
                raise
            print(f"Edge TTS retry {attempt+1}: {str(exc)[:200]}", flush=True)
            await asyncio.sleep(4 * (attempt+1))

async def main():
    durations=[]
    for i,(line,caption,scene) in enumerate(BEATS):
        mp3=OUT/f"edge_voice_{i:02}.mp3"
        await synthesize(line,mp3)
        wav=OUT/f"edge_audio_{i:02}.wav"
        run("ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(mp3),
            "-af","atempo=1.25","-ac","1","-ar","24000",str(wav))
        sec=duration(wav)
        durations.append(sec)
        draw_frame(i,(line,caption,scene))
        print(f"Edge voice {i+1}/{len(BEATS)}: {sec:.2f}s",flush=True)
    # One independently synthesized scene per line: timings match each scene boundary.
    captions=[];now=0.0
    video_lines=[];audio_lines=[]
    for i,((spoken,_,_),dt) in enumerate(zip(BEATS,durations)):
        captions.append(f"{i+1}\n{timestamp(now)} --> {timestamp(now+dt)}\n{spoken}\n")
        video_lines.extend([f"file 'frame_{i:02}.png'",f"duration {dt:.6f}"])
        audio_lines.append(f"file 'edge_audio_{i:02}.wav'")
        now+=dt
    video_lines.append(f"file 'frame_{len(BEATS)-1:02}.png'")
    (OUT/"edge_video_slides.txt").write_text("\n".join(video_lines)+"\n",encoding="utf-8")
    (OUT/"edge_audio_list.txt").write_text("\n".join(audio_lines)+"\n",encoding="utf-8")
    (OUT/"edge_captions.srt").write_text("\n".join(captions),encoding="utf-8")
    (OUT/"edge_script.txt").write_text("\n".join(x[0] for x in BEATS),encoding="utf-8")
    (OUT/"edge_metadata.json").write_text(json.dumps({
        "title":"착한 사람은 왜 항상 상처받을까? | 아들러 심리학 1화",
        "description":"아들러 심리학의 과제의 분리를 바탕으로 한 재구성 콘텐츠입니다. #생활알고리즘 #shorts",
        "voice":VOICE,"speed":SPEED,"status":"REVIEW_ONLY","uploaded":False,
        "generated_at_kst":datetime.now(ZoneInfo("Asia/Seoul")).isoformat()
    },ensure_ascii=False,indent=2),encoding="utf-8")
    run("ffmpeg","-y","-hide_banner","-loglevel","error","-safe","0","-f","concat",
        "-i",str(OUT/"edge_audio_list.txt"),"-c:a","pcm_s16le",str(OUT/"edge_hyunsu_voice.wav"))
    run("ffmpeg","-y","-hide_banner","-loglevel","error","-safe","0","-f","concat",
        "-i",str(OUT/"edge_video_slides.txt"),"-i",str(OUT/"edge_hyunsu_voice.wav"),
        "-map","0:v:0","-map","1:a:0","-vf","fps=30,format=yuv420p",
        "-c:v","libx264","-preset","veryfast","-crf","23",
        "-c:a","aac","-b:a","128k","-t",f"{now:.4f}","-movflags","+faststart",
        str(OUT/"adler_01_hyunsu.mp4"))
    print(f"Created alternative-voice MP4: {now:.1f}s. Not uploaded.",flush=True)

if __name__=="__main__":
    asyncio.run(main())
