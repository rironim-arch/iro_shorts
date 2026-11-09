"""Single consistent Korean voice for down-jacket Short; user-approved alternative to Charon."""
from pathlib import Path
from gtts import gTTS
import json
P=Path("out_down_puffer_alt");P.mkdir(exist_ok=True)
lines=[
"다운패딩, 무조건 드라이클리닝 맡기시나요? 사실 그게 정답은 아닙니다.",
"가장 먼저 안쪽 세탁 라벨을 확인하세요. 물세탁이 가능하다면 집에서도 관리할 수 있어요.",
"다운 전용 세제로 찬물에 부드럽게 세탁하세요. 세탁기 사용은 제품 표시를 따르고, 섬유유연제와 표백제는 피하세요.",
"진짜 중요한 건 건조입니다. 건조기 사용이 허용됐다면 낮은 온도로 충분히 말리고, 뭉친 솜털을 풀어주세요.",
"다만 특수 소재나 장식이 있거나 물세탁 금지 표시가 있다면 제품 안내를 따르세요. 모든 패딩에 같은 방법을 쓰면 안 됩니다.",
"내 패딩의 세탁 라벨부터 확인! 도움이 됐다면 구독과 좋아요, 생활알고리즘."
]
for i,s in enumerate(lines):
 gTTS(text=s,lang="ko",slow=False).save(str(P/f"scene_{i:02}.mp3"))
 print("SAVED",i,flush=True)
(P/"script.json").write_text(json.dumps(lines,ensure_ascii=False,indent=2),encoding="utf8")
