# 생활알고리즘 Shorts 자동 제작 (시험 버전)

Google Gemini TTS 음성 + 크게 읽히는 한국어 자막 + 9:16 영상으로 쇼츠 1편을 제작합니다. 노트북을 계속 켜둘 필요 없이 GitHub Actions에서 수동으로 실행할 수 있습니다.

## 현재 구현된 범위

- 한국어 생활정보 예시 대본 1개: **샴푸는 많이 쓰면 더 깨끗할까?**
- Gemini TTS를 사용한 한국어 음성 생성 (Charon 기본값)
- 한국어 큰 자막이 포함된 1080×1920 슬라이드 영상과 CTA
- MP4, 대본 TXT, 자막 SRT를 Actions Artifacts로 다운로드

**아직 자동 게시 / 매일 2편 예약은 켜지 않았습니다.** 음성·화면·비용을 시험 검증한 뒤에 추가할 예정입니다.

## 준비

GitHub 저장소 → Settings → Secrets and variables → Actions → Repository secrets 에 `GEMINI_API_KEY`를 등록해야 합니다. 키 값은 코드나 Issues에 올리지 마세요.

## 테스트하기

1. GitHub의 Actions 탭으로 이동
2. `생활알고리즘 숏츠 1개 테스트` 워크플로 선택
3. `Run workflow` 누르기
4. 완료되면 해당 실행의 **Artifacts**에서 `saenghwal-algorithm-short`을 다운로드
5. MP4 재생 후 음성·자막·폰트 확인

Gemini 무료 API는 할당량·가용성에 따라 호출 제한이 생길 수 있으며 비용은 본인의 Google AI Studio 프로젝트 설정을 확인하세요. 음성 및 내용의 정확성, 상업적 사용조건, 유튜브 게시 전 검수가 필요합니다.

## 향후 연동

1. 생활정보 주제·대본 다양화 및 사실 검수
2. 매일 2개 예약 실행 (GitHub Actions 일정)
3. 유튜브 채널 OAuth 인증 및 YouTube Data API (업로드 쿼터 / 비공개 제한 확인)
4. 먼저 비공개 업로드 검증 후 예약 공개 전환

## 개발 실행

```bash
pip install -r requirements.txt
python generate.py
```

시스템에 `ffmpeg`와 한국어 Noto Sans CJK 글꼴이 필요합니다. 기본 실행은 온라인 Gemini TTS API를 호출합니다.
