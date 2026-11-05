# 생활알고리즘 – 하루 2개 숏츠 자동 제작

> 첫 테스트 영상이 사용자 확인을 거쳐 재생되었습니다. **자동 영상 제작 기능은 설정했지만, 유튜브 자동 업로드는 아직 연결하지 않았습니다.**

## 현재 작동 방식

- **제작 시간**: 매일 오전 9시 14분 / 오후 6시 14분 (한국시간, KST)
- **실행 위치**: GitHub Actions, 컴퓨터를 켜 둘 필요 없음
- **대본**: `topics.json`에 준비된 60개 생활정보 대본에서 날짜·시간에 따라 1개씩 선택
- **음성**: Gemini 2.5 Flash Preview TTS, 한국어 남성 음성 (Charon)
- **영상**: Python + Pillow + FFmpeg, 1080×1920, 큰 자막, 생활알고리즘 표시와 구독·좋아요 안내
- **결과물**: 매 실행의 Actions Artifacts → MP4, 자막 SRT, 대본 TXT, 업로드용 메타데이터 JSON
- **보관**: Artifacts는 생성 후 14일 보관

60개를 하루 2개씩 사용하므로 **30일 뒤에는 대본이 반복됩니다.** 반복 없이 계속 새로운 영상을 만들려면 주제 목록 확장 또는 정확성 검토가 포함된 생성 단계가 추가로 필요합니다.

자막 시간은 음성 길이를 문장별 글자 수로 나눈 **대략적인 추정치**입니다. 단어별 정밀 싱크는 아직 구현되지 않았습니다. 현재 영상은 생성형 이미지 대신 도형·텍스트를 활용한 템플릿 방식입니다.

## 무료 사용과 실패 가능성

- Google Gemini 2.5 Flash Preview TTS는 현재 개발자 API 무료 등급을 제공하지만 요청 한도가 있고, 이를 넘으면 실행에 실패할 수 있습니다.
- 비용, 무료 한도, 모델 지원 여부는 Google AI Studio에서 반드시 확인하세요.
- GitHub Actions의 예약 실행은 서버 혼잡으로 지연될 수 있습니다.
- 영상 내용 및 표현은 업로드 전 확인하는 것이 좋습니다.

## 수동 테스트

1. [GitHub Actions](https://github.com/rironim-arch/iro_shorts/actions) 열기
2. `생활알고리즘 매일 2개 자동 제작` 선택
3. `Run workflow`로 실행 (`topic_number`에 1~60 지정 가능)
4. 실행이 초록색 `Success`면 `Artifacts`에서 MP4 내려받기

## 예정된 다음 단계: YouTube 예약 업로드

1. YouTube Data API v3 사용 설정
2. YouTube 채널의 **OAuth 2.0 업로드 권한** 획득 (Gemini API 키만으로는 업로드 불가능)
3. 사용자 인증 토큰을 GitHub Secret으로 보관
4. **비공개 영상 1개** 업로드 테스트 및 올바른 채널인지 확인
5. 필요하면 검토 승인 과정을 유지한 채 예약 공개 활성화

API 키·OAuth 토큰은 소스코드에 직접 입력하거나 채팅에 게시하지 마세요.

## 주요 파일

- `topics.json`: 60개 정보 주제와 문장
- `generate.py`: 음성·이미지·MP4·자막 생성
- `requirements.txt`: 파이썬 의존성
- `.github/workflows/test-short.yml`: 매일 2회 예약 실행 및 수동 테스트

