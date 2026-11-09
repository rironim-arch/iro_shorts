"""Single-speaker Korean backup for 6-scene caffeine short; Charon replacement needed.
Keep audio segments for precise scene-level sync.
"""
from pathlib import Path
from gtts import gTTS
import json
OUT=Path("out_caffeine_backup");OUT.mkdir(exist_ok=True)
LINES=[
 "저녁에 커피 한 잔 마셨는데, 왜 새벽까지 잠이 안 올까요? 카페인이 뇌의 졸음 신호를 가리기 때문입니다.",
 "우리가 깨어 있는 동안 뇌에는 아데노신이 쌓여요. 이 물질은 이제 쉴 시간이라고 알려주는 신호죠.",
 "그런데 카페인이 아데노신의 작용을 막습니다. 피로가 사라진 게 아니라, 졸음을 덜 느끼는 거예요.",
 "더 중요한 건 지속 시간! 카페인은 보통 다섯에서 여섯 시간이 지나도, 몸에 절반 정도 남을 수 있어요.",
 "그래서 늦은 오후 커피도 밤잠을 방해할 수 있습니다. 잠을 설치면 잠들기 최소 여섯 시간 전엔 카페인을 피하고, 민감하면 더 일찍 끊어보세요.",
 "오늘의 생활알고리즘! 도움이 됐다면 구독과 좋아요, 꼭 부탁드려요."
]
for i,line in enumerate(LINES):
 gTTS(line,lang="ko",slow=False).save(str(OUT/f"scene_{i:02d}.mp3"))
 print("DONE",i,flush=True)
(OUT/"script.json").write_text(json.dumps(LINES,ensure_ascii=False,indent=2),encoding="utf8")
