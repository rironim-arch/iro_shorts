# 생활알고리즘 — 검증형 숏츠 제작 시스템

> **2026-11-09 채널 제작 고정 기준:** [SHORTS_PRODUCTION_STANDARD.md](SHORTS_PRODUCTION_STANDARD.md) — Gemini Charon / 또렷한 1.25배속 / 대본·실사·편집의 실질적 독창성 / 매 편 '구독과 좋아요' 음성·자막 엔딩 필수. 동일 인트로·로고·엔딩은 사용 가능하지만 본문은 새로운 정보와 연출이 필요하며, 남의 영상을 약간 바꿔 올리는 방식은 금지합니다. 유튜브 수익화 승인을 보장하지 않습니다.\n\n2026-11-07 개편. 기존 단일 템플릿과 60편 순환은 수익화용으로 권장하지 않습니다. 현재 유튜브 자동 업로드는 없으며, 모든 영상은 검토용 초안입니다.

## 핵심 개선
- 출처 있는 정보: 영상마다 핵심 사실과 근거 링크, 시청자가 해볼 행동요령 필수. 링크가 있다는 사실은 자동 사실검증이 아니므로 사람이 검토해야 합니다.
- 반복 방지: 비슷한 대본·도입·마무리는 자동 사전 검사, 4가지 편집 형식과 주제별 도식을 사용.
- 큰 자막과 음성 싱크: 현수(Edge 한국어 남성) 음성, 1.25배속, 1080x1920. 문장별 실제 음성 길이에 따라 화면과 SRT 시간 표시.
- 게시 승인: 유튜브 업로드 기능 없음. 자료 확인과 사용자 승인 후 별도 게시.
- 주제 소진 후 반복 금지: 4편을 모두 만들면 소재를 새로 추가해야 함.

## 새로 제작하기
1. https://github.com/rironim-arch/iro_shorts/actions/workflows/editorial-review-short.yml
2. '생활알고리즘 검증형 숏츠 제작 (검토용)' 선택 후 Run workflow 클릭.
3. topic_id 101~104 중 하나 선택.
4. 완료된 실행의 Artifacts에서 MP4, WAV, SRT, 대본, 출처, 품질 검사 JSON 다운로드.
5. 출처의 내용과 대본의 일치, 음성/자막, 저작권, 과장표현, AI 공개 필요 여부 등을 검토한 뒤 게시.

## 첫 4개 검증형 주제
- 101: 락스+식초 혼합 경고 (CDC)
- 102: 전자레인지 금속 용기 예외와 주의 (FDA)
- 103: 냉장고 온도 확인 (FDA)
- 104: 멀티탭 소비전력과 과부하 (ESFI)

## 파일
- editorial_topics.json — 근거 링크, 대본, 장면 계획 포함.
- editorial_quality.py — 구조, 반복, 분량, 출처 메타데이터 확인. 사실 여부 자체는 자동 판정 불가.
- create_editorial_short.py — 영상별 차별화 도식과 음성/자막 싱크.
- .github/workflows/editorial-review-short.yml — 수동 검토용 제작.
- topics.json, generate.py, .github/workflows/test-short.yml — 과거 실험 버전. 단일 템플릿·반복 구조로 본편 제작에 비권장.

## YouTube 참고
https://support.google.com/youtube/answer/1311392 — 비진정성/반복 콘텐츠
https://support.google.com/youtube/answer/14328491?hl=ko — AI 콘텐츠 공개

AI를 사용했다고 무조건 수익화가 불가능한 것은 아닙니다. 각 영상의 실질적 교육 가치가 달라야 하며, 자동 품질 검사만으로 수익화 적격 여부를 보증할 수 없습니다.

**현황: 제작 초안만 생성. 자동 업로드와 제휴 링크 게시 없음.**
