"""Two medically grounded dog skin Shorts, with single continuous Charon narrations and Pexels licensed moving dog video."""
import requests,subprocess,os,random,re,json,wave,sys,time
from pathlib import Path
import imageio_ffmpeg
from google import genai
from google.genai import types

O=Path("dog_shorts_assets"); O.mkdir(exist_ok=True)
FF=imageio_ffmpeg.get_ffmpeg_exe()
DATA={
"clocidin":{
  "title":"강아지 클로시딘 소독제, 원액 그대로 바르면 안 됩니다!",
  "text":[
    "강아지가 피부를 긁는다고 클로시딘부터 바르고 있나요?",
    "클로시딘은 클로르헥시딘 성분이 들어간 동물용 피부 소독제입니다.",
    "하지만 중요한 사실! 클로시딘 원액을 그대로 바르면 안 됩니다.",
    "5퍼센트 제품의 허가된 피부 소독법은, 원액 100밀리리터를 물 10리터에 희석하는 방식입니다.",
    "다른 제품은 농도가 다를 수 있으니 제품 설명과 수의사 지시를 먼저 확인하세요.",
    "클로르헥시딘은 일부 피부 표면 세균 관리에 도움을 주지만, 모든 피부병을 치료하는 만능약은 아닙니다.",
    "눈과 귓속, 깊은 상처에는 사용하지 마세요. 바른 부위를 핥지 않도록 주의해야 합니다.",
    "진물이나 심한 붉어짐, 악취, 반복되는 가려움은 소독보다 원인 진단이 먼저입니다.",
    "생활알고리즘. 유익했다면 구독과 좋아요!"
  ],
  "captions":[
    "긁는다고 소독제부터?",
    "클로시딘 = 클로르헥시딘",
    "원액 그대로 사용 금지",
    "5% 원액 100mL + 물 10L",
    "제품 농도 · 수의사 지시 확인",
    "모든 피부병의 치료제는 아니다",
    "눈 · 귓속 · 깊은 상처 주의",
    "진물 · 냄새 · 재발 시 진료",
    "생활알고리즘 | 구독 · 좋아요"
  ]
},
"skindisease":{
  "title":"강아지 피부병, 5가지 원인을 구별해야 합니다!",
  "text":[
    "강아지가 발을 계속 핥고 몸을 긁는다면? 원인이 하나가 아닙니다.",
    "첫 번째, 알레르기성 피부염. 꽃가루, 집먼지진드기, 음식이나 벼룩 때문에 가려울 수 있어요.",
    "두 번째, 세균성 농피증. 붉은 뾰루지나 딱지, 고름이 생길 수 있습니다.",
    "세 번째, 말라세지아 효모성 피부염. 기름진 피부와 특유의 냄새, 발이나 귀 가려움이 나타날 수 있어요.",
    "네 번째, 피부사상균증. 동그란 탈모와 각질이 나타날 수 있고, 사람에게 옮기도 합니다.",
    "다섯 번째, 기생충성 피부질환. 옴진드기, 모낭충, 벼룩이 원인일 수 있습니다.",
    "이 밖에도 갑상선 같은 호르몬 문제가 피부와 털에 영향을 줄 수 있어요.",
    "겉으로 보이는 증상만으로는 정확히 구분하기 어렵습니다.",
    "피부 도말이나 긁기 검사 등으로 원인을 확인해야 맞는 치료를 할 수 있어요.",
    "생활알고리즘. 유익했다면 구독과 좋아요!"
  ],
  "captions":[
    "발 핥기 · 몸 긁기, 원인은?",
    "① 알레르기성 피부염",
    "② 세균성 농피증",
    "③ 말라세지아 효모성 피부염",
    "④ 피부사상균증 (곰팡이)",
    "⑤ 기생충성 피부질환",
    "호르몬 질환도 원인일 수 있다",
    "증상만으로 확진 불가",
    "피부 검사 → 원인별 치료",
    "생활알고리즘 | 구독 · 좋아요"
  ]
}
}
CLIPS=[
 (6235179,"vet_small_dog"),
 (9252747,"small_dog_bath"),
 (6131725,"dog_rinsing"),
 (32248361,"dog_scratches_ear"),
 (5001190,"dog_licks_paw"),
 (6714792,"dog_paw_winter"),
 (6235185,"vet_ear_exam"),
 (6234592,"vet_dog_table"),
 (7469782,"vet_help"),
 (6131723,"dog_grooming"),
 (6235751,"vet_holding_dog"),
 (6816874,"vet_dog_check")
]
def cmd(*parts,timeout=160):
 return subprocess.run([FF,"-y","-hide_banner","-loglevel","error",*map(str,parts)],check=True,timeout=timeout)
def voice(name,d,client):
 prompt=("Speak this Korean educational narration as ONE continuous take with a consistent calm male voice. "
 "Use natural Korean pronunciation, warm clear diction. Do not introduce yourself, skip words, repeat anything, or add any commentary. "
 "The LAST line contains the only request for subscription/like; never say that phrase earlier. "
 "No music, no bracketed stage directions. Read only the script exactly.\n\n"+ "\n".join(d["text"]))
 resp=client.models.generate_content(model="gemini-2.5-flash-preview-tts",contents=prompt,
 config=types.GenerateContentConfig(response_modalities=["AUDIO"],
 speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
 rawmeta=next(p.inline_data for p in resp.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data)
 raw=rawmeta.data
 dst=O/f"{name}_charon_full.wav"
 if raw[:4]==b"RIFF": dst.write_bytes(raw)
 else:
  match=re.search(r"rate=(\d+)",rawmeta.mime_type or "")
  with wave.open(str(dst),"wb") as w:
   w.setnchannels(1);w.setsampwidth(2);w.setframerate(int(match.group(1)) if match else 24000);w.writeframes(raw)
 fast=O/f"{name}_charon_125.wav"
 cmd("-i",dst,"-af","atempo=1.25","-ac","1","-ar","24000",fast)
 with wave.open(str(fast),"rb") as w: sec=w.getnframes()/w.getframerate()
 if sec<22 or sec>125:raise ValueError(f"Bad length {name}:{sec}")
 d["duration"]=sec
 d["voice"]="Gemini Charon single take, 1.25x"
 (O/f"{name}.json").write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8")
 print("VOICE_READY",name,round(sec,2),flush=True)
def urls(id):
 list_=[]
 for size in ("720_1280","1280_720","720_1366","1080_1920","1920_1080","960_540","540_960","1280_800","720_480","1080_2048"):
  for fps in (25,30,24,50,60):
   list_.append(f"https://videos.pexels.com/video-files/{id}/{id}-hd_{size}_{fps}fps.mp4")
 list_.append(f"https://www.pexels.com/download/video/{id}/")
 return list_
def fetch(id,name,s):
 for u in urls(id):
  try:
   h=s.head(u,allow_redirects=True,timeout=2.5)
   if h.status_code!=200:continue
   if not ("video" in h.headers.get("Content-Type","") or "octet" in h.headers.get("Content-Type","")):continue
   b=int(h.headers.get("Content-Length",0))
   if b>58_000_000:continue
   tmp=O/f"raw_{id}.mp4";amount=0
   with s.get(u,stream=True,timeout=(5,60)) as r:
    r.raise_for_status()
    with tmp.open("wb") as f:
     for chunk in r.iter_content(500000):
      amount+=len(chunk)
      if amount>58_000_000:raise RuntimeError("Too large")
      f.write(chunk)
   dest=O/f"clip_{name}.mp4"
   cmd("-i",tmp,"-t","10","-vf","scale=960:960:force_original_aspect_ratio=increase,crop=960:960,fps=24,format=yuv420p","-an","-c:v","libx264","-crf","26","-preset","veryfast",dest)
   tmp.unlink(missing_ok=True)
   print("CLIP_READY",name,id,dest.stat().st_size,flush=True)
   return True
  except Exception as e:
   (O/f"raw_{id}.mp4").unlink(missing_ok=True)
 print("CLIP_UNAVAILABLE",name,id,flush=True)
 return False
def main():
 client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
 for name,data in DATA.items():
  voice(name,data,client);time.sleep(1)
 s=requests.Session();s.headers["User-Agent"]="Mozilla/5.0"
 status={name:fetch(id,name,s) for id,name in CLIPS}
 (O/"footage_status.json").write_text(json.dumps(status,indent=2))
 (O/"references.txt").write_text(
   "Primary veterinary references:\n"
   "https://vcahospitals.com/know-your-pet/chlorhexidine-topical\n"
   "https://www.merckvetmanual.com/integumentary-system/integumentary-system-introduction/dermatological-problems-in-animals\n"
   "https://www.merckvetmanual.com/integumentary-system/atopic-skin-conditions-in-dogs-and-cats/atopic-dermatitis-in-dogs\n"
   "https://www.merckvetmanual.com/integumentary-system/dermatophytosis/dermatophytosis-in-dogs-and-cats\n"
   "Korean product-specific approved dilution: https://www.dongsipharm.com/vet/medicines/clocidin/\n"
   "All videos are illustrative licensed Pexels actual moving footage, not documentary footage of diagnosed animals or actual chlorhexidine treatment.\n"
   "Pexels license: https://www.pexels.com/license/\n"+
   "\n".join(f"{name}: https://www.pexels.com/video/{id}/" for id,name in CLIPS),encoding="utf-8")
 print("ASSETS_COMPLETE",flush=True)
if __name__=="__main__":main()
