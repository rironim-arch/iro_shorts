import os, pathlib
from gtts import gTTS
p=pathlib.Path("out_tooth_gtts");p.mkdir(exist_ok=True)
lines=[
 "칫솔질, 세게 문지르면 더 깨끗할까요? 사실 중요한 건 힘보다 방법입니다.",
 "미국치과의사협회 권고에 따르면, 부드러운 칫솔을 잇몸 경계에 약 45도로 대세요. 세게 누르지 마세요.",
 "칫솔은 짧고 부드럽게 앞뒤로 움직이고, 치아 바깥쪽과 안쪽, 씹는 면까지 모두 닦습니다.",
 "앞니 안쪽은 칫솔을 세워 위아래로 움직이세요. 불소치약으로 하루 두 번, 한 번에 약 2분입니다.",
 "양치 후에는 치약을 뱉으세요. 바로 물로 여러 번 헹구지 않는 편이 불소 보호에 더 유리합니다.",
 "치실이나 치간칫솔로 치아 사이도 하루에 한 번 관리하세요.",
 "오늘부터 바꿔보세요! 도움이 됐다면 구독과 좋아요! 생활알고리즘, 알아두면 쓸모 있는 생활상식."
]
for i,line in enumerate(lines):
 print("START",i,flush=True)
 gTTS(line,lang="ko",slow=False).save(str(p/f"scene_{i:02}.mp3"))
 print("SAVED",i,flush=True)
