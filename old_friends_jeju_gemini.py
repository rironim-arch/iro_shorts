#!/usr/bin/env python3
"""Gemini TTS story: two Korean male friends, one 72, ending at Jeju. Per-voice one take; align by actual ASR words."""
from pathlib import Path
import os,re,time,wave,json,subprocess,difflib,unicodedata,math,shutil
from google import genai
from google.genai import types
from faster_whisper import WhisperModel
OUT=Path("old_friends_jeju_tts");OUT.mkdir(exist_ok=True)
TURNS=[["son","아버지! 그 돈은 노후에 쓰려고 모으신 거잖아요!",0],["narrator","일흔두 살 아버지는 친구 장례식에 다녀온 다음 날, 은행에서 적금 하나를 해지했습니다.",0],["narrator","낡은 옷을 기워 입고 외식도 아끼던 분이었죠. 놀란 아들은 급히 집으로 찾아왔습니다.",1],["son","아버지, 갑자기 돈은 왜 찾으셨어요? 누구한테 빌려주시는 건 아니죠?",0],["father","아니다. 여행 좀 가려고 그런다.",0],["son","여행이요? 아버지가요?",0],["narrator","아버지에게는 반평생을 함께한 친구가 있었습니다. 둘은 젊은 시절 공장에서 같이 일했고, 서로의 결혼식에도 함께했죠.",2],["narrator","살림을 꾸리고 아이들을 키우느라 바빠도, 만나면 늘 똑같은 약속을 했습니다.",3],["friend","우리 일흔 되면 제주도 가자. 바다 보면서 소주도 한잔하고.",4],["father","그래. 그땐 일 다 내려놓고 꼭 가자.",4],["narrator","그런데 일흔이 되니 병원에 갈 일이 생겼고, 손주를 돌봐야 할 때도 있었어요. 이번만 미루자고 하다, 또 한 해가 갔습니다.",4],["narrator","얼마 전, 친구에게서 전화가 왔습니다.",5],["friend","우리 이번 봄엔 정말 가자. 더 늦기 전에.",5],["father","그래, 이번에는 꼭 가자.",5],["narrator","하지만 봄이 오기 전, 그 친구가 세상을 떠났습니다.",6],["son","아버지… 그 여행을 이제 혼자 가시겠다고요?",0],["father","그 친구가 마지막에 그러더라. 우린 왜 그렇게 내일만 기다렸을까, 하고.",6],["narrator","아버지는 서랍에서 젊은 시절 두 사람이 함께 찍은 사진을 꺼냈습니다.",7],["father","이 녀석 사진이라도 데리고 가야지. 약속은 지켜야 하지 않겠냐.",7],["narrator","며칠 뒤, 아버지는 제주도 바닷가에 섰습니다. 주머니 속 사진을 꺼내 파도 소리 앞에 조용히 들어 보였죠.",8],["father","친구야… 우리 드디어 왔다.",8],["narrator","사람은 언제나 다음을 약속합니다. 하지만 그 다음이 누구에게나 오는 건 아니더군요.",8],["narrator","아직 함께 걸을 수 있을 때, 좋은 사람과 오늘을 누리세요.",8],["cta","이 이야기가 마음에 남으셨다면 구독과 좋아요 부탁드립니다.",8]]
VOICES={"narrator":"Kore","father":"Enceladus","son":"Orus","friend":"Charon","cta":"Kore"}
INSTRUCTIONS={
"narrator":"You are a mature warm Korean female drama storyteller; steady natural delivery, never too fast and no voice changes. Convey years of friendship without artificial sorrow.",
"father":"You are a believable Korean man of seventy two, with a lower, slightly breathy voice; natural elderly dignity, not cartoon or exaggerated rasp. Emotions: confusion, nostalgia, grief, quiet joyful closure. Strong stable identity.",
"son":"You are his adult Korean son in his early forties, natural conversational concerned and slightly surprised male Korean voice; Orus, do not overact.",
"friend":"You are a 72 year old Korean man and the lifelong male friend of the father. Charon male low calm friendly voice, little teasing and affection. You are NOT the son or narrator. Natural older man's conversational Korean.",
"cta":"Warm settled Korean female narrator Kore, one standard end-of-story subscribe statement delivered ONCE, no extra speech."
}
def sh(*a):subprocess.run(list(map(str,a)),check=True)
def norm(x):return re.sub(r"[^가-힣a-z0-9]","",unicodedata.normalize("NFKC",x)).lower()
assert len(TURNS)==24 and sum("구독과 좋아요" in x[1] for x in TURNS)==1
api=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
meta={}
def generate(role,voice,lines,key=None):
    key=key or role
    prompt=(INSTRUCTIONS[role]+" "
       "Generate exactly one continuous recording of all Korean paragraphs below in the order given. "
       "Speak only those sentences. DO NOT invent extra lines, omit any word, introduce an actor, announce numbers or repeat the last line. "
       "Keep one and the same recognizable character voice throughout, stable timbre, loudness, microphone distance. "
       "Pause clearly for about 0.65 seconds after EVERY paragraph; this is ESSENTIAL for precise editing. "
       "Speak the COMPLETE last sentence including the ending syllables; leave 0.5 seconds silence after the last sound. "
       "No background sound, music, breathing performance or special effects.\n\n"+
       "\n\n".join(lines))
    if role=="narrator" and len(lines)==1:
        prompt=("당신은 성숙한 한국어 여성 나레이터 Kore입니다. 아래 대본 한 문장만 또박또박 읽으세요. 목소리는 차분하고 따뜻하게 유지하세요. 다른 말이나 음악은 절대 넣지 마세요. 마지막 글자까지 읽으세요. 대본: "+lines[0])
    packet=None
    for attempt in range(4):
        try:
            rep=api.models.generate_content(model="gemini-2.5-flash-preview-tts",contents=prompt,
               config=types.GenerateContentConfig(response_modalities=["AUDIO"],
               speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
               prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)))))
            for can in rep.candidates:
                for part in can.content.parts:
                    p=getattr(part,"inline_data",None)
                    if p and getattr(p,"data",None):
                        packet=p;break
                if packet:break
            if packet is None:raise RuntimeError("No Gemini audio")
            break
        except Exception as e:
            print("TTS_RETRY",role,attempt,str(e)[:220],flush=True)
            if attempt==3:raise
            time.sleep(8*(attempt+1))
    raw=OUT/f"{key}_raw.wav"
    if packet.data[:4]==b"RIFF":raw.write_bytes(packet.data)
    else:
        m=re.search(r"rate=(\d+)",packet.mime_type or "")
        with wave.open(str(raw),"wb") as w:
            w.setnchannels(1);w.setsampwidth(2);w.setframerate(int(m.group(1)) if m else 24000);w.writeframes(packet.data)
    clean=OUT/f"{key}_master.wav"
    sh("ffmpeg","-y","-v","error","-i",raw,
      "-af","loudnorm=I=-17:TP=-2:LRA=10","-ar","24000","-ac","1",clean)
    with wave.open(str(clean),"rb") as w:d=w.getnframes()/w.getframerate()
    print("VOICE_GENERATED",role,voice,round(d,3),len(lines),flush=True)
    if d<3 or d>160:raise RuntimeError(f"Abnormal {role} duration {d}")
    return clean,d
for role,voice in VOICES.items():
    lines=[t[1] for t in TURNS if t[0]==role]
    if role=="narrator":
        groups=[lines[0:2],lines[2:4],lines[4:6],lines[6:8],lines[8:9],lines[9:10],lines[10:11]]
        for partnum,small in enumerate(groups):
            partname="narrator_part"+str(partnum)
            prev=__import__("pathlib").Path("fullparts")/(partname+"_master.wav")
            if not prev.exists():raise RuntimeError("Missing finished Kore part "+str(prev))
            audio=OUT/(partname+"_master.wav")
            shutil.copy2(prev,audio)
            with wave.open(str(audio),"rb") as w:secs=w.getnframes()/w.getframerate()
            print("REUSING_FINISHED_KORE_TAKE",partname,secs,flush=True)
            meta[partname]={"voice":voice,"source":audio.name,"seconds":secs,"lines":small}
    else:
        prev=__import__("pathlib").Path("fullparts")/(role+"_master.wav")
        if not prev.exists():raise RuntimeError("Missing existing male actor "+str(prev))
        audio=OUT/(role+"_master.wav")
        shutil.copy2(prev,audio)
        with wave.open(str(audio),"rb") as w:secs=w.getnframes()/w.getframerate()
        print("REUSE_FINISHED_ACTOR",role,secs,flush=True)
        meta[role]={"voice":voice,"source":audio.name,"seconds":secs,"lines":lines}
print("LOADING_WHISPER_FOR_PRECISE_CUTS",flush=True)
model=WhisperModel("small",device="cpu",compute_type="int8",cpu_threads=4,num_workers=2)
files={}
qa=[]
for role,m in meta.items():
    wav=OUT/m["source"];seconds=m["seconds"];lines=m["lines"]
    segments,info=model.transcribe(str(wav),language="ko",word_timestamps=True,beam_size=4,
       vad_filter=False,condition_on_previous_text=False)
    segments=list(segments)
    words=[{"w":w.word,"s":float(w.start),"e":float(w.end)}
           for seg in segments for w in (seg.words or []) if w.word.strip()]
    spoken=" ".join(seg.text.strip() for seg in segments)
    (OUT/f"{role}_transcript.txt").write_text(spoken,encoding="utf8")
    if not words:raise RuntimeError(f"ASR got zero words for {role}")
    expected=[(i,norm(w)) for i,line in enumerate(lines) for w in line.split() if norm(w)]
    observed=[norm(w["w"]) for w in words]
    match=difflib.SequenceMatcher(None,[s for _,s in expected],observed,autojunk=False)
    corr={}
    for b in match.get_matching_blocks():
        for k in range(b.size):corr[b.a+k]=b.b+k
    matchratio=sum(len(expected[i][1]) for i in corr)/max(1,sum(len(x[1]) for x in expected))
    print("ASR_COVERAGE",role,round(matchratio,3),"words",len(words),flush=True)
    if matchratio<0.40:raise RuntimeError(f"Bad transcript match: {role}:{matchratio}")
    # Verify every line boundary: identify first and last ASR words mapped into each script line.
    detected=[]
    for li,line in enumerate(lines):
        ids=[words[j] for i,j in sorted(corr.items()) if expected[i][0]==li]
        if not ids:raise RuntimeError(f"Missing entire TTS line {role}:{li}")
        anchorstart=min(w["s"] for w in ids)
        anchorend=max(w["e"] for w in ids)
        detected.append({"start":anchorstart,"end":anchorend,"matched_words":len(ids)})
    roleclips=[]
    for li,line in enumerate(lines):
        prevend=detected[li-1]["end"] if li>0 else 0
        nextstart=detected[li+1]["start"] if li+1<len(lines) else seconds
        first=detected[li]["start"];last=detected[li]["end"]
        # Leave 0.10 seconds before first recognized syllable and 0.20 after final syllable.
        # Use midpoint of actual intervening silent gap to avoid cutting the next utterance.
        start=max(prevend+0.02 if li else 0.0,first-0.13)
        end=min(nextstart-0.03 if li+1<len(lines) else seconds,last+0.24)
        # Last recognized syllables must remain whole even where Gemini runs dialogue together.
        end=min(seconds,max(end,last+0.13))
        if end-last<0.04:raise RuntimeError(f"Potential final syllable clipping: {role} {li}")
        if end-start<.6:raise RuntimeError(f"Invalid TTS segment {role}:{li}")
        file=OUT/f"{role}_{li:02d}.wav"
        sh("ffmpeg","-y","-v","error","-ss",f"{start:.4f}","-i",wav,
           "-t",f"{end-start:.4f}","-ar","24000","-ac","1",file)
        roleclips.append({"file":file.name,"seconds":round(end-start,3),"raw_start":start,"raw_end":end,
                         "detected_end":last,"last_word_buffer_seconds":round(end-last,3),
                         "text":line,"asr_anchors":detected[li]})
        # Check expected FINAL Korean word against original ASR text for this segment, tolerate minor ASR spellings
        lasttoken=norm(line.split()[-1])
        local_observed=norm(" ".join(w["w"] for w in words if start-.15<=w["s"]<end+.1))
        endhit=lasttoken in local_observed
        if not endhit:
           print("ASR_LAST_WORD_WARNING",role,li,lasttoken,local_observed[-65:],flush=True)
        qa.append({"role":role,"line_index":li,"endhit":endhit,"last_word":lasttoken,
                   "last_word_buffer_seconds":round(end-last,3)})
    m["segments"]=roleclips
    print("ROLE_SPLIT",role,len(roleclips),flush=True)
# Validate last line presence in each role. CTA must unambiguously contain ending word.
for role,m in meta.items():
    asr=(OUT/f"{role}_transcript.txt").read_text(encoding="utf8")
    if role=="cta" and not all(w in norm(asr) for w in ["구독","좋아요","부탁드립니다"]):
        raise RuntimeError("CTA last phrase missing")
    if role=="father" and not ("드디어" in norm(asr) and "왔다" in norm(asr)):
        raise RuntimeError("Father closing line missing")
partkeys=[key for key in meta if key.startswith("narrator_part")]
partkeys.sort(key=lambda k:int(k.split("part")[-1]))
all_narrator=[seg for k in partkeys for seg in meta[k]["segments"]]
if len(all_narrator)!=len([t for t in TURNS if t[0]=="narrator"]):raise RuntimeError("Missing Kore narrative clip")
meta["narrator"]={"voice":"Kore","segments":all_narrator,"source_take_count":len(partkeys)}
# Build source timeline, source clips not speed adjusted; client video synthesis applies atempo=1.25
used={r:0 for r in VOICES}
ordered=[]
for pos,(role,text,scene) in enumerate(TURNS):
    li=used[role];used[role]+=1
    item=meta[role]["segments"][li]
    ordered.append({"turn":pos,"role":role,"voice":VOICES[role],"text":text,"scene":scene,
                   "audio_file":item["file"],"duration":item["seconds"],
                   "last_word_buffer_sec":item["last_word_buffer_seconds"]})
output={"video":"Friends Funeral Trip to Jeju","original_fiction":True,"story_version":1,
  "audio_raw_seconds":round(sum(x["duration"] for x in ordered),3),"target_tempo":1.25,
  "audio_takes":{"narrator":7,"father":1,"son":1,"friend":1,"cta":1},
  "turns":ordered,"roles":meta,"qa":qa,"important_note":"Do not force-truncate; preserve every word and add trailing 0.18s if needed."}
(OUT/"manifest.json").write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")
print("PREPARED_AND_QA_COMPLETE",len(ordered),"original_voice_seconds",output["audio_raw_seconds"],flush=True)
