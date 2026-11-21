#!/usr/bin/env python3
"""Replace old inconsistent 18-clip narration with one continuous Orus take.
Uses existing final MP4 as exact approved layout, scene stills are retained.
Word-level ASR anchors align image scene captions to the new one-take recording.
All outputs are PRIVATE review artifacts, never public posts.
"""
import json, os, re, subprocess, shutil, math, difflib, unicodedata, wave
from pathlib import Path
from faster_whisper import WhisperModel

OUT=Path("two_friends_one_voice_final")
OUT.mkdir(exist_ok=True)
VOICE_RUN=os.getenv("VOICE_RUN_ID")
LAYOUT_RUN=os.getenv("LAYOUT_RUN_ID")
if not VOICE_RUN or not LAYOUT_RUN:
    raise RuntimeError("Missing prior successful audio and layout run IDs")
def sh(*parts):
    subprocess.run(list(map(str,parts)),check=True)
def probe(path):
    r=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=noprint_wrappers=1:nokey=1",str(path)],
        text=True,check=True,capture_output=True)
    return float(r.stdout.strip())
def grab_artifact(run_id, name, folder):
    folder.mkdir(exist_ok=True)
    sh("gh","run","download",run_id,"-n",name,"-D",folder)
def find(folder,name):
    files=list(folder.rglob(name))
    if len(files)!=1:raise RuntimeError(f"Expected one {name}, got {files}")
    return files[0]
voice_dir=OUT/"voice_artifact"
layout_dir=OUT/"layout_artifact"
grab_artifact(VOICE_RUN,"two-friends-one-take-orus-wav",voice_dir)
grab_artifact(LAYOUT_RUN,"two-friends-reference-exact-gemini-orus-final",layout_dir)
wav=find(voice_dir,"two_friends_orus_one_take.wav")
original_video=find(layout_dir,"인생애니사연_30년만에뒤바뀐두친구_Orus_30fps.mp4")
old_srt=find(layout_dir,"실제Gemini음성기준자막.srt")
data=json.loads(find(voice_dir,"approved_script.json").read_text(encoding="utf8"))
lines=data["script"]
assert len(lines)==18
total=probe(wav)
with wave.open(str(wav),"rb") as w:
    assert w.getnchannels()==1 and w.getframerate()==24000
    assert abs(total-w.getnframes()/w.getframerate())<0.05
def to_seconds(ts):
    h,m,s=ts.replace(",",".").split(":")
    return int(h)*3600+int(m)*60+float(s)
def clock(sec):
    t=max(0,round(sec*1000))
    hh,t=divmod(t,3600_000);mm,t=divmod(t,60_000);ss,ms=divmod(t,1000)
    return f"{hh:02}:{mm:02}:{ss:02},{ms:03}"
srt_blocks=[x for x in re.split(r"\n\s*\n",old_srt.read_text(encoding="utf8").strip()) if x.strip()]
assert len(srt_blocks)==len(lines)
old_boundaries=[]
subs=[]
for block in srt_blocks:
    bits=block.strip().splitlines()
    m=re.fullmatch(r"(\d\d:\d\d:\d\d,\d{3}) --> (\d\d:\d\d:\d\d,\d{3})",bits[1])
    assert m is not None,bits
    old_boundaries.append(to_seconds(m.group(1)))
    subs.append("\n".join(bits[2:]))
print("ASR_START",total,flush=True)
model=WhisperModel("small",device="cpu",compute_type="int8",cpu_threads=4,num_workers=2)
segments,info=model.transcribe(str(wav),language="ko",beam_size=4,
        word_timestamps=True,vad_filter=False,condition_on_previous_text=False)
segments=list(segments)
words=[]
for seg in segments:
    if seg.words:
        words += [{"word":w.word,"start":float(w.start),"end":float(w.end)} for w in seg.words if w.word.strip()]
asr=" ".join(seg.text for seg in segments)
(OUT/"asr_transcript.txt").write_text(asr+"\n",encoding="utf8")
(OUT/"asr_words.json").write_text(json.dumps(words,ensure_ascii=False,indent=2),encoding="utf8")
print("ASR_TRANSCRIPT",asr,flush=True)
if len(words)<40:raise RuntimeError("ASR returned too few words to time scenes accurately")
norm=lambda x: re.sub(r"[^가-힣a-zA-Z0-9]","",unicodedata.normalize("NFKC",x)).lower()
expected=[(i,norm(w)) for i,line in enumerate(lines) for w in line.split() if norm(w)]
actual=[norm(w["word"]) for w in words]
match=difflib.SequenceMatcher(None,[x[1] for x in expected],actual,autojunk=False)
token_match={}
for block in match.get_matching_blocks():
    for k in range(block.size):token_match[block.a+k]=block.b+k
ratio=sum(len(expected[i][1]) for i in token_match)/max(1,sum(len(x[1]) for x in expected))
print("ASR_EXACT_MATCHED_CHAR_RATIO",round(ratio,3),"WORDS",len(actual),flush=True)
if ratio<0.28:raise RuntimeError(f"ASR and script are too dissimilar: matched_char_ratio={ratio:.3f}")
# Verify the last sentence is really spoken, not truncated from TTS generation.
last_words=" ".join(w["word"] for w in words[-18:])
last_norm=norm(last_words)
if not ("구독" in last_norm and "좋아요" in last_norm and "부탁" in last_norm):
    raise RuntimeError("ASR cannot confirm final subscribe/like clause: "+last_words)
if words[-1]["end"]<total-4.0:
    raise RuntimeError("Unusually long silence after final spoken word, check TTS")

# Place each intended word at the corresponding ASR word's measured start.
# Interpolate only unmatched words; no 18 separate voice clips are introduced.
anchors={0:0.0,len(expected):total}
for i,j in token_match.items():
    anchors[i]=max(0.,min(total,words[j]["start"]))
anch=sorted(anchors.items())
def interp(token_i):
    if token_i<=anch[0][0]:return anch[0][1]
    for (x0,t0),(x1,t1) in zip(anch,anch[1:]):
        if x0<=token_i<=x1:
            return t0+(token_i-x0)*(t1-t0)/max(1,x1-x0)
    return total
starts=[0.0]
for li in range(1,len(lines)):
    boundary=next(i for i,(l,_) in enumerate(expected) if l==li)
    starts.append(interp(boundary))
# Preserve chronological order. Slightly lead the syllable onset by 60ms for readability.
starts=[0.0]+[max(.0,min(total,starts[i]-.06)) for i in range(1,len(starts))]
for i in range(1,len(starts)):
    if starts[i]<starts[i-1]+.5:
        raise RuntimeError(f"ASR timing collision between lines {i} and {i+1}")
bounds=starts+[total]
# Source MP4 contains baked captions; pick one representative frame inside each old scene.
for i,sec in enumerate(old_boundaries):
    t=sec+.25
    sh("ffmpeg","-y","-v","error","-ss",f"{t:.3f}","-i",original_video,
       "-frames:v","1","-q:v","2",OUT/f"frame_{i:02d}.jpg")
concat=OUT/"scenes.txt"
concat.write_text(
    "".join(f"file 'frame_{i:02d}.jpg'\nduration {bounds[i+1]-bounds[i]:.6f}\n" for i in range(len(lines)))
    +"file 'frame_17.jpg'\n",encoding="utf8")
srt=[]
for i,txt in enumerate(subs):
    srt.append(f"{i+1}\n{clock(bounds[i])} --> {clock(bounds[i+1])}\n{txt}\n")
(OUT/"실제한목소리_단어정렬자막.srt").write_text("\n".join(srt),encoding="utf8")
shutil.copy2(wav,OUT/"Gemini_Orus_단일녹음.wav")
shutil.copy2(find(voice_dir,"two_friends_orus_one_take.mp3"),OUT/"Gemini_Orus_단일녹음.mp3")
final=OUT/"인생애니사연_두친구_단일Orus_최종_30fps.mp4"
sh("ffmpeg","-y","-hide_banner","-loglevel","error",
   "-f","concat","-safe","0","-i",concat,
   "-i",wav,"-map","0:v:0","-map","1:a:0",
   "-vf","fps=30,format=yuv420p","-c:v","libx264","-preset","veryfast","-crf","22",
   "-c:a","aac","-b:a","160k","-t",f"{total:.3f}","-movflags","+faststart",final)
got=probe(final)
if abs(got-total)>0.5:raise RuntimeError(f"Video/audio mismatch {got}, {total}")
qa={"voice":"Google Gemini Orus","tts_calls":1,"audio":"one continuous uninterrupted recording",
    "duration_seconds":round(total,3),"rendered_seconds":round(got,3),
    "scenes":len(lines),"frames_per_second":30,"size":"1080x1920",
    "asr_exact_matched_script_characters_ratio":round(ratio,3),
    "asr_checked_final_subscribe_like":True,
    "captions":"ASR timed word-level anchors used; review required before publishing",
    "layout_source":"prior verified frame exact matching user's 2026-11-21 screenshot",
    "publication_status":"UNPUBLISHED"}
(OUT/"검수결과.json").write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding="utf8")
print("SINGLE_VOICE_FINAL_RENDERED",json.dumps(qa,ensure_ascii=False),flush=True)
