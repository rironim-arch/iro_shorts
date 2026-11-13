"""Generate TWO original single-take Charon Shorts narrations and fetch licensed real moving B-roll.
Sources and script are original; do NOT publish to social accounts.
"""
from pathlib import Path
import json,re,wave,requests,subprocess,os,random,time
from google import genai
from google.genai import types
import imageio_ffmpeg

OUT=Path("two_shorts_assets"); OUT.mkdir(exist_ok=True)
FF=imageio_ffmpeg.get_ffmpeg_exe()
SCRIPTS={
"heater":{
  "title":"온풍기 8시간 켜면? 전기장판과 15배 차이?",
  "lines":[
    "겨울에 온풍기, 밤새 8시간 켜면 전기요금 얼마나 나올까요?",
    "정격 소비전력 100와트 전기장판과, 1500와트 온풍기를 비교해볼게요.",
    "하루 8시간씩, 한 달 30일. 같은 조건으로 계산해봤습니다.",
    "전기장판은 한 달 24킬로와트시.",
    "온풍기는 무려 360킬로와트시입니다.",
    "전력 사용량이 15배나 차이 나는 셈이죠.",
    "그런데 이 숫자가 곧바로 전기요금은 아닙니다.",
    "집에서 원래 쓰던 전기량과 누진 구간에 따라 실제 요금은 달라져요.",
    "또 두 제품 모두 온도조절 기능이 작동하면 실제 사용량이 줄 수 있습니다.",
    "중요한 건 제품에 적힌 소비전력과 사용 시간! 온풍기는 잠잘 때 켜두지 마세요.",
    "생활알고리즘. 유익했다면 구독과 좋아요!"
  ],
  "caption":[
    "온풍기, 밤새 틀면 얼마?",
    "전기장판 100W  vs  온풍기 1,500W",
    "하루 8시간 × 30일",
    "전기장판 24kWh / 월",
    "온풍기 360kWh / 월",
    "사용량 차이 15배!",
    "사용량 = 전기요금은 아니다",
    "누진 구간 · 평소 사용량 중요",
    "온도조절 시 실제 사용량 변동",
    "소비전력 확인! 취침 중 온풍기 OFF",
    "생활알고리즘 | 구독 · 좋아요"
  ]
},
"battery":{
  "title":"휴대폰 밤새 충전하면 배터리 망가질까?",
  "lines":[
    "휴대폰을 밤새 충전기에 꽂아두면 배터리가 망가질까요?",
    "요즘 갤럭시는 100퍼센트가 되면 충전을 멈추도록 제어합니다.",
    "그럼 밤새 꽂아둬도 배터리에는 아무 영향이 없을까요?",
    "꼭 그렇지는 않습니다. 100퍼센트에 오래 머무르거나 열이 많이 나면 배터리 수명에 부담이 될 수 있어요.",
    "해결 방법은 생각보다 간단합니다.",
    "갤럭시 설정에서 배터리를 열고, 배터리 보호를 켜보세요.",
    "최대 보호 모드에서는 충전 상한을 설정할 수 있습니다.",
    "일부 모델에서는 80, 85, 90, 95퍼센트 중 선택할 수 있죠.",
    "수면 중 배터리 보호 기능을 쓰면 잠잘 때 충전을 제한하고, 기상 직전에 100퍼센트까지 채우기도 합니다.",
    "단, 휴대폰 모델과 소프트웨어 버전에 따라 메뉴와 기능이 달라집니다.",
    "생활알고리즘. 유익했다면 구독과 좋아요!"
  ],
  "caption":[
    "밤새 충전, 배터리 망가질까?",
    "100%에 도달하면 충전 제어",
    "그럼 아무 문제 없을까?",
    "높은 충전 상태 · 발열 주의",
    "해결 방법은?",
    "설정 → 배터리 → 배터리 보호",
    "최대 모드로 상한 설정",
    "80 · 85 · 90 · 95%",
    "수면 중 보호: 기상 전 100%",
    "모델 · One UI 버전별 차이",
    "생활알고리즘 | 구독 · 좋아요"
  ]
}}
STOCK={
"heater":[
  (4058896,"blanket_cozy"),
  (4058899,"blanket_close"),
  (5983690,"bedroom"),
  (6951586,"sleep_blanket")
],
"battery":[
  (36017452,"charging_nightstand"),
  (4820379,"cable_plug"),
  (4201544,"battery_settings"),
  (8165880,"phone_touch"),
  (7947495,"phone_usage")
]}
def ff(*args,timeout=150):
    subprocess.run([FF,"-y","-hide_banner","-loglevel","error",*map(str,args)],check=True,timeout=timeout)
def voice_one_take(name,data,client):
    script="\n".join(data["lines"])
    print("VOICE_START",name,flush=True)
    r=client.models.generate_content(
      model="gemini-2.5-flash-preview-tts",
      contents=("Read only the following complete Korean script as ONE continuous narration, in your consistently calm, friendly, professional Korean male voice. DO NOT add or repeat any words, introduction, or calls to action. The ONLY subscribe-and-like phrase is at the very end of the script. Natural pauses between lines; no music. \nSCRIPT START\n"+script+"\nSCRIPT END"),
      config=types.GenerateContentConfig(response_modalities=["AUDIO"],speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
    inline=next(p.inline_data for p in r.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data)
    raw=inline.data
    d=OUT/f"{name}_charon_original.wav"
    if raw[:4]==b"RIFF":d.write_bytes(raw)
    else:
      match=re.search(r"rate=(\d+)",inline.mime_type or "")
      rate=int(match.group(1)) if match else 24000
      with wave.open(str(d),"wb") as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(raw)
    fast=OUT/f"{name}_charon_125.wav"
    ff("-i",d,"-af","atempo=1.25","-ac","1","-ar","24000",fast)
    with wave.open(str(fast),"rb") as w:dur=w.getnframes()/w.getframerate()
    if dur<25 or dur>115:raise RuntimeError("Voice duration suspicious: "+str(dur))
    meta={"title":data["title"],"lines":data["lines"],"caption":data["caption"],"duration":dur,"voice":"Gemini 2.5 Flash Charon","speed":1.25}
    (OUT/f"{name}_manifest.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
    print("VOICE_READY",name,dur,flush=True)
def sources(id):
    qs=[]
    for w,h in [(720,1280),(1080,1920),(720,1366),(1280,720),(960,540),(540,960),(960,960),(1080,2048),(1280,800),(540,960),(720,480)]:
       for fps in (25,30,24,50,60):
          qs.append(f"https://videos.pexels.com/video-files/{id}/{id}-hd_{w}_{h}_{fps}fps.mp4")
    qs.append(f"https://www.pexels.com/download/video/{id}/")
    return qs
def download(stock_id,name,prefix,session):
    dst=OUT/f"{prefix}_{name}.mp4"
    for j,url in enumerate(sources(stock_id)):
      try:
        head=session.head(url,timeout=(3,6),allow_redirects=True)
        if head.status_code!=200:continue
        ctype=head.headers.get("Content-Type","")
        size=int(head.headers.get("Content-Length","0"))
        if ("video" not in ctype and "octet" not in ctype) or size>62_000_000:continue
        print("STOCK_HIT",prefix,name,url,size,flush=True)
        original=OUT/f"_download_{stock_id}.mp4"
        total=0
        with session.get(url,stream=True,timeout=(6,70)) as r:
          r.raise_for_status()
          with original.open("wb") as f:
            for b in r.iter_content(524288):
              if b:
                total+=len(b)
                if total>62_000_000:raise RuntimeError("too large")
                f.write(b)
        ff("-i",original,"-t","10","-vf","scale=960:960:force_original_aspect_ratio=increase,crop=960:960,fps=24,format=yuv420p","-an","-c:v","libx264","-crf","25","-preset","veryfast",dst)
        original.unlink(missing_ok=True)
        print("STOCK_READY",prefix,name,dst.stat().st_size,flush=True)
        return True
      except Exception as e:
        (OUT/f"_download_{stock_id}.mp4").unlink(missing_ok=True)
    print("STOCK_MISSING",prefix,name,flush=True)
    return False
def main():
    client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    for name,d in SCRIPTS.items():
       voice_one_take(name,d,client)
    session=requests.Session();session.headers["User-Agent"]="Mozilla/5.0"
    ok={}
    for section,clips in STOCK.items():
       for stock_id,clip_name in clips:
          ok[section+"_"+clip_name]=download(stock_id,clip_name,section,session)
    (OUT/"stock_status.json").write_text(json.dumps(ok,indent=2))
    (OUT/"sources.txt").write_text(
      "Video clips: Pexels free licensed stock https://www.pexels.com/license/\n"+
      "\n".join(f"{n}_{label}: https://www.pexels.com/video/{id}/" for n,clips in STOCK.items() for id,label in clips)+
      "\nFacts: Samsung battery protection https://www.samsung.com/sec/support/galaxy-battery/battery-protection-tip/\n"+
      "Heater electricity numbers: arithmetic 0.1kW/1.5kW * 8h * 30d; illustrative continuous rated-power use, not bills.\n"+
      "Safety: https://www.nfpa.org/education-and-research/home-fire-safety/heating\n",
      encoding="utf-8")
    print("DONE",flush=True)
if __name__=="__main__":main()
