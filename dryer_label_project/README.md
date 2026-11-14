# 건조기 넣기 전, 이 표시부터

1080×1920 / 30 fps. 기존 사용자 요청에 따라 Gemini Charon 한 번의 연속 내레이션에 1.25배속을 한 번 적용한 다음, 실제 음성의 Whisper 단어 구간에 자막을 맞춥니다.

## 재현
Python 3.11, FFmpeg, Noto Sans CJK 폰트. 의존성: google-genai>=1,<3; Pillow>=10,<13; requests; numpy; faster-whisper.
GEMINI_API_KEY는 환경 변수로만 사용합니다. 키를 파일이나 저장소에 넣지 않습니다.
`python render.py`

## 편집
script.txt: 나레이션. render.py의 PHRASES: 원문을 유지한 자막 구간. output/asr.json: 실제 음성 인식과 단어 구간. output/cues.json: 최종 자막 타임라인. assets/charon_original.wav: 생성 원음. assets/charon_125.wav: 최종 음성 시간축.

## 근거와 영상 사용
GINETEX의 ISO 3758:2023 취급 기호 설명: https://www.ginetex.net/GB/labelling/care-symbols.asp
LG전자 수축/손상 및 라벨 확인 안내: https://www.lge.co.kr/support/solutions-20151827436317
국제 기호 중 건조기 사용 금지 및 저온 표시만 설명합니다. 국내외 다른 표시 체계와 제품 문구는 해당 제조사 안내를 따릅니다. 면 소재나 니트라는 이름만으로 모든 의류를 분류하지 않습니다.

Pexels의 8756891, 7792705, 7855136, 8756886 영상은 설명용 자료 화면입니다. 실제 수축 실험, 특정 의류의 성분 검증, 제조사 권장 코스의 시연이 아닙니다. 영상 라이선스: https://www.pexels.com/license/
기호 그림은 설명을 위한 코드 그래픽입니다.

## 검수 범위
자동 음성 인식 대조, 실제 단어 구간 기반 자막 타이밍, 인코딩 전체 디코딩, 글자 폭 및 대표 장면 검사를 사용합니다. 청취 검수 여부는 quality.json에 별도로 기록합니다.
구독·좋아요는 마지막 발화에 한 번만 포함됩니다. 유튜브 등 외부 플랫폼 게시 작업은 포함하지 않습니다.
