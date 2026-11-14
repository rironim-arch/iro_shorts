"""Repair repeated mid-story CTA: Kore narrates all exposition, villain Gacrux has direct speech only; CTA standalone at end.
One uninterrupted order; use speech-to-text audit to detect accidental CTA before finale.
"""
import os,re,wave,json,subprocess,time
from pathlib import Path
import imageio_ffmpeg
from google import genai
from google.genai import types
OUT=Path("webtoon_cta_repair_audio")
OUT.mkdir(exist_ok=True)
FF=imageio_ffmpeg.get_ffmpeg_exe()
HERO=[
[
"그 여자가 처음으로 제게 커피를 건넨 날, 저는 오히려 불안했습니다.",
"그 여자는 3년 동안 같은 회사에서 저를 괴롭히던 선배였거든요.",
"입사 첫날부터 업무를 물어보면 한숨을 쉬었고,",
"점심시간이면 저만 빼놓고 동료들과 식당에 갔습니다."
],
[
"제가 밤새 준비한 자료를 자기 이름으로 보고한 적도 있었죠.",
"그래도 참았습니다. 열심히 일하면 언젠가는 인정받을 거라고 생각했으니까요.",
"그런데 어느 월요일 아침, 이상한 일이 벌어졌습니다."
],
[
"늘 차갑던 사람이 갑자기 웃으며 다가왔습니다.",
"처음엔 조금 기뻤습니다. 드디어 저를 동료로 인정해 주는 걸까요?",
"하지만 다음 날, 그 이유를 알게 됐습니다.",
"제가 신설 부서의 팀장 후보로 추천됐다는 소식이 회사에 퍼진 겁니다.",
"그 여자는 제가 자신의 상사가 될 수도 있다는 걸 이미 알고 있었던 거죠.",
"그제야 깨달았습니다.",
"그 여자가 달라진 건 저를 보는 마음이 아니라, 제 위치를 바라보는 눈이었다는 걸요.",
"사람의 진심은 필요할 때의 친절보다, 아무것도 바라지 않을 때의 태도에서 드러납니다."
],
["이 내용이 마음에 드셨으면 구독과 좋아요 해주세요."]
]
VILLAIN=[
["그런 것도 몰라요? 언제까지 가르쳐줘야 해요?"],
["커피 드실래요? 오늘 점심은 저랑 같이 먹어요."]
]
assert not any("구독" in " ".join(b) or "좋아요" in " ".join(b) for b in HERO[:-1]),"STRICT no early CTA"
cli=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
def save_pcm(r,path):
    part=next(p.inline_data for p in r.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data)
    data=part.data
    if data.startswith(b"RIFF"):path.write_bytes(data)
    else:
        m=re.search(r"rate=(\d+)",part.mime_type or "")
        sr=int(m.group(1)) if m else 24000
        with wave.open(str(path),"wb") as f:
            f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr);f.writeframes(data)
def synth(lines,voice,path,cta=False):
    # Deliberately no call-to-action phrase in prompt for non-CTA segments.
    basic=("Read the following Korean text EXACTLY and ONLY as printed, once, in a single continuous take. "
           "Natural warm mature female voice with understated emotion, like a genuine office worker recalling an awkward workplace incident. "
           "Keep the same stable speaking character throughout. No introductions, no instructions spoken aloud, no extra words, no music. "
           "Make natural sentence pauses. Do not substitute words. ")
    if voice=="Gacrux":
        basic=("A female Korean office coworker speaks this ONE short direct quote only. "
               "The tone is mildly haughty and dismissive when criticizing, but artificially polite for coffee offer. "
               "Only read the supplied words exactly, no tags, no introduction, no additional words. ")
    if cta:
        basic=("Read only the SINGLE Korean line below as the same warm friendly Korean female narrator Kore. "
               "No beginning greeting, no extras, no repeats, no musical jingle. Just this one line. ")
    prompt=basic+"\nKOREAN SPOKEN TEXT:\n"+ "\n".join(lines)
    for attempt in range(4):
        try:
            r=cli.models.generate_content(model="gemini-2.5-flash-preview-tts",contents=prompt,
              config=types.GenerateContentConfig(response_modalities=["AUDIO"],speech_config=types.SpeechConfig(
                 voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)))))
            save_pcm(r,path)
            break
        except Exception as e:
            print("TTS_RETRY",voice,attempt,str(e)[:200],flush=True)
            if attempt==3:raise
            time.sleep(8*(attempt+1))
    tmp=path.with_name(path.stem+"_125.wav")
    subprocess.run([FF,"-y","-loglevel","error","-i",str(path),"-af","atempo=1.25","-ar","24000","-ac","1",str(tmp)],check=True)
    path.unlink()
    with wave.open(str(tmp),"rb") as f:dur=f.getnframes()/f.getframerate()
    if dur<1:raise RuntimeError("Suspiciously short generated audio")
    return tmp,dur
def audit(path,index,isfinal):
    # Content-level verification: use Gemini audio understanding to check whether any CTA is spoken.
    prompt=(
     "Transcribe all Korean words actually SPOKEN in this audio, in their order. "
     "Do not add an intro, commentary or missing words from anywhere else. "
     "Output ONLY the Korean transcript with no other text."
    )
    try:
        r=cli.models.generate_content(model="gemini-2.5-flash",contents=[
           types.Part.from_text(text=prompt),
           types.Part.from_bytes(data=path.read_bytes(),mime_type="audio/wav")])
        trans=(r.text or "").strip()
        (OUT/f"audit_{index}.txt").write_text(trans,encoding="utf-8")
        norm=re.sub(r"\s+","",trans)
        mention=("구독" in norm or "좋아요" in norm)
        if isfinal and not ("구독" in norm and "좋아요" in norm):
            print("WARNING_FINAL_TRANSCRIPT_NO_CTA",index,trans[:220],flush=True)
        if not isfinal and mention:
            raise RuntimeError(f"EARLY_CTA_IN_AUDIO segment={index} transcript={trans[:300]}")
        print("AUDIO_AUDIT",index,"cta",mention,"chars",len(trans),flush=True)
    except RuntimeError:raise
    except Exception as e:
        print("AUDIO_AUDIT_UNAVAILABLE",index,str(e)[:220],flush=True)
sequence=[
 ("Kore",HERO[0],False),
 ("Gacrux",VILLAIN[0],False),
 ("Kore",HERO[1],False),
 ("Gacrux",VILLAIN[1],False),
 ("Kore",HERO[2],False),
 ("Kore",HERO[3],True)
]
metadata=[]
for idx,(voice,lines,cta) in enumerate(sequence):
    fname=OUT/f"section_{idx}_{voice.lower()}.wav"
    wav,duration=synth(lines,voice,fname,cta)
    audit(wav,idx,cta)
    metadata.append({"index":idx,"voice":voice,"lines":lines,"duration":round(duration,3),"audio":wav.name,"cta":cta})
    print("SECTION_READY",idx,voice,round(duration,2),"cta",cta,flush=True)
assert sum(int(x["cta"]) for x in metadata)==1 and metadata[-1]["cta"],"CTA must appear last only"
(OUT/"manifest.json").write_text(json.dumps({"sections":metadata,"speed":1.25,"cta_policy":"ONLY final segment, Kore, once"},ensure_ascii=False,indent=2),encoding="utf-8")
print("ALL_AUDIO_VERIFIED_AND_READY",round(sum(x["duration"] for x in metadata),2),flush=True)
