import os, json, wave, subprocess, time, re
from pathlib import Path
from openai import OpenAI
LINES=[{"scene":"market","text":"열다섯 해를 함께한 까미는, 마지막 순간에도 나를 집까지 데려다주었습니다. 꿈속에서요. 어릴 적 엄마를 따라간 시골 장터. 낡은 종이상자 안에는 강아지 다섯 마리가 있었습니다. 다른 아이들은 서로 장난쳤지만, 유독 까맣고 작은 한 마리만 구석에서 떨고 있었죠."},{"scene":"market","text":"이상하게 그 아이에게서 눈을 뗄 수 없었습니다. 엄마, 나 저 까만 강아지 데려가면 안 돼? 그냥… 내가 지켜줘야 할 것 같아."},{"scene":"child","text":"그날 작은 강아지를 품에 안고 돌아왔습니다. 아프지 말고, 까만 털이 꼭 밤하늘 같아서, 이름을 까미라고 지었죠. 그런데 이상한 일이었습니다. 까미가 자랄수록, 나를 지켜주는 건 오히려 까미였습니다."},{"scene":"gate","text":"학교에서 속상한 일이 생겨 혼자 울던 날에는 말없이 곁에 앉아 있었고, 캄캄한 시골길이 무서울 때면 언제나 내 앞에서 걸어주었습니다. 늦게 돌아오는 날이면 대문 앞에서 나를 기다렸습니다."},{"scene":"night","text":"나는 어느새 어른이 되었고, 까만 까미의 얼굴에도 흰 털이 하나둘 늘었습니다. 함께한 지 열다섯 해. 까미는 이제 혼자 일어서는 것조차 힘겨워했습니다. 그날 밤, 까미 곁에 이불을 깔고 누웠습니다."},{"scene":"dream","text":"까미야… 오늘은 내가 네 옆에 있을게. 까미의 등을 쓰다듬다 잠든 나는, 아주 오래전 살던 시골길을 꿈꾸었습니다. 어두운 길 뒤편에서 익숙한 발소리가 들렸습니다."},{"scene":"dream","text":"뒤돌아보니, 까미였습니다. 늙고 아픈 모습이 아닌, 젊고 건강한 모습이었죠. 까미야! 너 여기 있었구나. 까미는 꼬리를 흔들더니, 어린 시절처럼 내 앞에서 집까지 걸어주었습니다."},{"scene":"farewell","text":"대문 앞에 도착하자 까미는 멈춰 서서 나를 오래 바라보았습니다. 까미야, 안 들어와? 까미는 조용히 꼬리를 흔들고, 빛이 비치는 길로 천천히 걸어갔습니다."},{"scene":"cry","text":"그 순간 잠에서 깼습니다. 창문으로 아침 햇살이 들어오고 있었습니다. 그런데 내 곁의 까미는… 더 이상 숨을 쉬지 않았습니다. 까미야… 내가 널 지켜준다고 생각했는데, 평생 나를 지켜준 건 너였구나."},{"scene":"heaven","text":"마지막 꿈에서까지 날 집에 데려다줘서 고마워. 나보다 먼저 가서 기다리게 해서 미안해. 거기선 아프지 말고 마음껏 뛰어놀아. 까미야… 우리, 언젠가 천국에서 꼭 다시 만나자."},{"scene":"cta","text":"내가 지켜주려고 데려온 작은 강아지는, 열다섯 해 동안 나의 가장 든든한 친구였습니다. 이 이야기가 마음에 남으셨다면 구독과 좋아요 부탁드립니다."}]
out=Path("kkami_openai");out.mkdir(exist_ok=True)
api=os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_TTS_API_KEY")
if not api:raise RuntimeError("OPENAI_API_KEY_NOT_CONNECTED")
client=OpenAI(api_key=api, timeout=28.0, max_retries=1)
records=[];t=0
for i,item in enumerate(LINES,1):
    path=out/f"clip_{i:02d}.wav"
    if i == 1:print("OPENAI_TEST_REQUEST_STARTED",flush=True)
    try:
        data=client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="shimmer",
            input=item["text"],
            response_format="wav",
            speed=1.05,
            instructions="Speak Korean naturally as a warm adult woman recalling her beloved black dog Kkami. Restrained deeply sincere storytelling with gentle sorrow, steady clear diction, not robotic or exaggerated. The woman's inner child dialogue may sound tender. No sound effects. Speak every syllable and every ending. No extra words."
        )
        path.write_bytes(data.content)
        if i == 1:print("OPENAI_TEST_REQUEST_SUCCEEDED",flush=True)
    except Exception as ex:
        print("OPENAI_REQUEST_FAILED line=",i,"type=",type(ex).__name__,"message=",str(ex)[:350],flush=True)
        raise
    p=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",str(path)],capture_output=True,text=True)
    if p.returncode:raise RuntimeError(p.stderr)
    d=float(p.stdout.strip())
    if not (1.0<d<55):raise RuntimeError("bad duration "+str(d))
    records.append(dict(i=i,scene=item["scene"],text=item["text"],file=path.name,start=round(t,4),end=round(t+d,4),duration=round(d,4),words=[]))
    t+=d
    print("OPENAI_AUDIO_OK",i,round(d,2),"total",round(t,2),flush=True)
(out/"manifest.json").write_text(json.dumps({"duration":round(t,4),"clips":records,"voice":"shimmer","tts_model":"gpt-4o-mini-tts","speed":1.05},ensure_ascii=False,indent=2),encoding="utf8")
(out/"concat.txt").write_text("\n".join("file '"+x["file"]+"'" for x in records)+"\n",encoding="utf8")
p=subprocess.run(["ffmpeg","-v","error","-y","-f","concat","-safe","0","-i",str(out/"concat.txt"),"-ar","24000","-ac","1",str(out/"full.wav")],capture_output=True,text=True)
if p.returncode:raise RuntimeError(p.stderr)
print("OPENAI_KKAMI_ALL_COMPLETE duration",round(t,2),flush=True)
