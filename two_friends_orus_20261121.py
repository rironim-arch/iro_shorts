#!/usr/bin/env python3
"""인생애니사연 두 친구: supplied approved storyboard + actual Gemini Orus speech.
Never publish. Output is an Actions artifact for private review.
"""
import json, os, re, subprocess, time, wave, urllib.request
from pathlib import Path
from google import genai
from google.genai import types

OUT=Path("two_friends_orus_output")
OUT.mkdir(exist_ok=True)
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
CAPTIONS=[
"민수야… 나 네 밑에서\n일하면 안 되겠냐?",
"대기업 부장 출신 준호가\n30년 지기 친구에게 꺼낸 말입니다.",
"가난했던 민수는 고등학교 졸업 후\n곧바로 공사현장에 나갔습니다.",
"반면 준호는 대학 졸업 후\n대기업에 입사했죠.",
"그때만 해도 민수는\n준호가 부러웠습니다.",
"30년 뒤, 민수는 배관과 용접을 익혀\n자기 사업체를 운영했습니다.",
"반면 준호는 부장까지 오른 뒤\n희망퇴직을 했습니다.",
"재취업은 번번이 실패했죠.",
"어느 날, 두 친구가\n술잔을 기울였습니다.",
"민수야… 너희 회사에\n사람 안 필요하냐?",
"자재 나르고, 청소하고,\n허드렛일부터 할게.",
"월급 적어도 괜찮아.\n나 진짜 다시 일하고 싶다.",
"너 부장까지 했잖아.\n자존심 안 상하겠냐?",
"솔직히 상하지. 그런데\n나만 바라보는 가족이 있잖아.",
"내 자존심보다\n가족들 밥벌이가 먼저더라.",
"월요일부터 나와.\n대신 처음부터 배워야 해.",
"가장의 용기는, 두려워도\n가족을 위해 다시 시작하는 것입니다.",
"이 이야기가 마음에 남으셨다면\n구독과 좋아요 부탁드립니다."
]
assert len(LINES)==len(CAPTIONS)==18
assert sum("구독과 좋아요" in s for s in LINES)==1
IMAGE_DURATIONS=[
3.507917,3.995128,4.774665,3.702801,3.800244,5.359318,
4.579781,3.020706,3.995128,4.092570,4.482339,4.482339,
4.190012,4.384896,5.359318,4.579781,5.749086,5.943971]
def sh(*args):
    subprocess.run(list(map(str,args)),check=True)
def duration(path):
    p=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
      "-of","default=noprint_wrappers=1:nokey=1",str(path)],capture_output=True,text=True,check=True)
    return float(p.stdout.strip())
def clock(s):
    n=round(s*1000); h,n=divmod(n,3600000);m,n=divmod(n,60000);sec,ms=divmod(n,1000)
    return f"{h:02}:{m:02}:{sec:02},{ms:03}"
url=os.environ.get("SOURCE_VIDEO_URL","")
if not url.startswith("https://"):
    raise RuntimeError("Source storyboard signed URL missing")
source=OUT/"source_silent.mp4"
urllib.request.urlretrieve(url,source)
if source.stat().st_size < 500_000:raise RuntimeError("Storyboard file incomplete")
p=subprocess.run(["ffprobe","-v","error","-select_streams","v:0",
 "-show_entries","stream=width,height","-of","csv=p=0",str(source)],capture_output=True,text=True,check=True)
assert p.stdout.strip()=="1080,1920",p.stdout
offset=0.
for i,d in enumerate(IMAGE_DURATIONS):
    sh("ffmpeg","-y","-v","error","-ss",f"{offset+min(0.8,d/2):.3f}","-i",source,
       "-frames:v","1","-q:v","2",OUT/f"scene_{i:02}.jpg")
    offset+=d
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
lengths=[]
for i,line in enumerate(LINES):
    emotion=(
      "A hesitant, earnest plea, humble and quiet." if i in (0,9,10,11,13,14)
      else "Brief measured, encouraging warmth." if i==15
      else "A steady moving life-story narration, sincere not theatrical."
    )
    prompt=(
      "Read only the quoted Korean sentence once in a mature, natural Korean male voice. "
      "Use Gemini's Orus voice consistently. "
      +emotion+
      " Pronounce every Korean word completely and clearly, with natural emotion. "
      "No extra words, no music, no narration of instructions, do not repeat. "
      "This is sentence number "+str(i+1)+" in one continuous story, keep consistent vocal level and pitch.\n"
      "SENTENCE:\n"+line
    )
    audio=None
    for attempt in range(5):
      try:
        resp=client.models.generate_content(
          model="gemini-2.5-flash-preview-tts",contents=prompt,
          config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
              prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Orus")))))
        for part in resp.candidates[0].content.parts:
          a=getattr(part,"inline_data",None)
          if a is not None and getattr(a,"data",None):audio=a;break
        if audio:break
        raise RuntimeError("Gemini returned empty audio")
      except Exception as err:
        print("TTS_RETRY",i+1,attempt+1,str(err)[:220],flush=True)
        if attempt==4:raise
        time.sleep(min(65,8*(attempt+1)))
    raw=OUT/f"line_{i:02}_raw.wav"
    if audio.data.startswith(b"RIFF"):raw.write_bytes(audio.data)
    else:
      rate=re.search(r"rate=(\d+)",audio.mime_type or "")
      with wave.open(str(raw),"wb") as o:
        o.setnchannels(1);o.setsampwidth(2)
        o.setframerate(int(rate.group(1)) if rate else 24000)
        o.writeframes(audio.data)
    if duration(raw)<0.8:raise RuntimeError(f"Line {i+1} voice is unexpectedly short")
    cleaned=OUT/f"line_{i:02}.wav"
    sh("ffmpeg","-y","-v","error","-i",raw,
       "-af","atempo=1.12,loudnorm=I=-17:TP=-2:LRA=11,apad=pad_dur=0.16",
       "-ac","1","-ar","24000","-sample_fmt","s16",cleaned)
    sec=duration(cleaned)
    if sec<0.8 or sec>16:raise RuntimeError(f"Suspicious TTS line duration {i+1}: {sec}")
    lengths.append(sec)
    print("ORUS_LINE_OK",i+1,round(sec,3),flush=True)
    # Remain safely below typical RPM limits while preserving same voice.
    if i+1<len(LINES):time.sleep(5)
(OUT/"audio_concat.txt").write_text(
    "".join(f"file 'line_{i:02}.wav'\n" for i in range(len(LINES))),encoding="utf8")
sh("ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",OUT/"audio_concat.txt",
   "-c:a","pcm_s16le",OUT/"gemini_orus_master.wav")
sh("ffmpeg","-y","-v","error","-i",OUT/"gemini_orus_master.wav",
   "-b:a","160k",OUT/"gemini_orus_master.mp3")
total=sum(lengths)
if not 40<total<115:raise RuntimeError(f"Unexpected total story duration {total}")
(OUT/"video_concat.txt").write_text(
    "".join(f"file 'scene_{i:02}.jpg'\nduration {d:.6f}\n" for i,d in enumerate(lengths))
    +f"file 'scene_{len(LINES)-1:02}.jpg'\n",encoding="utf8")
start=0.;srt=[]
for i,(txt,d) in enumerate(zip(CAPTIONS,lengths)):
    srt.append(f"{i+1}\n{clock(start)} --> {clock(start+d)}\n{txt}\n")
    start+=d
(OUT/"two_friends_actual_tts.srt").write_text("\n".join(srt),encoding="utf8")
# Every still already has its caption and approved navy/webtoon layout burned in.
sh("ffmpeg","-y","-hide_banner","-loglevel","error",
   "-f","concat","-safe","0","-i",OUT/"video_concat.txt",
   "-i",OUT/"gemini_orus_master.wav",
   "-map","0:v:0","-map","1:a:0",
   "-vf","fps=30,format=yuv420p",
   "-c:v","libx264","-preset","veryfast","-crf","23",
   "-c:a","aac","-b:a","160k",
   "-t",f"{total:.3f}","-movflags","+faststart",
   OUT/"two_friends_final_orus_30fps.mp4")
v=OUT/"two_friends_final_orus_30fps.mp4"
vsec=duration(v)
if abs(vsec-total)>0.5:raise RuntimeError(f"AV length mismatch {vsec} vs {total}")
qa={"name":"30년 만에 뒤바뀐 두 친구의 인생","voice":"Gemini Orus",
    "voice_speed":1.12,"width":1080,"height":1920,"fps":30,
    "duration_seconds":round(vsec,3),"scene_count":18,
    "note":"One-to-one audio clips and captions timed by each actual line WAV duration; source webtoon layout preserved.",
    "review_status":"REVIEW_REQUIRED_BEFORE_UPLOAD"}
(OUT/"qa.json").write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding="utf8")
# Do not include the unpublished source or intermediate images in output artifact.
for p in OUT.glob("scene_*.jpg"):p.unlink()
source.unlink()
print("FINAL_RENDER_QA",json.dumps(qa,ensure_ascii=False),flush=True)
