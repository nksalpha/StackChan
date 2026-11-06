# 서버 없는 직접 연결 펌웨어

NAS 서버를 거치지 않고, 기기가 클라우드 API를 바로 부른다.

```
말하는 동안  기기 ──음성 실시간 전송──▶ Deepgram (인식 + 말 끝 판정)
말 끝나면    기기 ──인식된 문장───────▶ DeepSeek (답변을 조금씩 받음)
문장마다     기기 ──문장──────────────▶ Google TTS (음성) → 바로 재생
```

- 펌웨어: `firmware/out/xiaozhi-stackchan-ko-direct-full.bin`
- 표정: 답변 맨 앞의 감정 태그(`[happy]` 등)를 읽어서 바꾼다.
- 대화 기억: 최근 6번 주고받은 내용까지. 전원을 끄면 지워진다.
- 키는 펌웨어 파일에 들어 있지 않다. 기기 설정 화면에서 넣으면 기기 안(NVS)에 저장된다.
- NAS 서버용 펌웨어(`xiaozhi-stackchan-ko-full.bin`)는 그대로 두었으니 언제든 바꿔 올릴 수 있다.

---

## 1. API 키 준비

키마다 이 기기 전용으로 새로 만들고, 쓸 수 있는 한도를 걸어 둔다. NAS 서버가 쓰는 키는 그대로 둔다.

### Deepgram
1. https://console.deepgram.com 로그인
2. 프로젝트 → **API Keys** → **Create a New API Key**
3. 이름은 `stackchan-device` 정도로. 권한은 기본(Member)이면 된다.
4. 만들어진 키를 복사해 둔다. 이 화면을 닫으면 다시 볼 수 없다.

### DeepSeek
1. https://platform.deepseek.com 로그인
2. **API keys** → **Create new API key** → 이름 입력 → 복사
3. DeepSeek은 충전식이라 충전한 금액 이상은 나가지 않는다.

### Google Cloud TTS
Google은 결제 수단 등록이 있어야 쓸 수 있다. 무료 사용량(Neural2 음성 월 100만 자)을 넘으면 자동으로 청구되니 아래 한도 설정을 꼭 한다.

1. https://console.cloud.google.com 에서 프로젝트를 하나 만든다 (예: `stackchan`).
2. 상단 검색창에 **Cloud Text-to-Speech API** → **사용(Enable)**
3. **API 및 서비스 → 사용자 인증 정보 → 사용자 인증 정보 만들기 → API 키**
4. 만들어진 키의 **키 제한**에서
   - API 제한사항: **Cloud Text-to-Speech API**만 선택
   - 저장
5. 한도 걸기 (둘 다 해 두면 안심)
   - **결제 → 예산 및 알림**: 월 예산을 1달러 정도로 잡고 알림 받기 (알림만 오고 사용을 막지는 않는다)
   - **API 및 서비스 → Cloud Text-to-Speech API → 할당량**: 분당 요청 수를 낮게 (예: 60) 잡아 두면 키가 새도 대량으로 쓰이지 않는다

하루 2시간 대화 기준 예상 사용량은 월 40만 자 정도라 무료 범위 안이다.

---

## 2. 플래싱

`docs/FLASH_WEB.md`와 같다. 파일만 `xiaozhi-stackchan-ko-direct-full.bin`으로 바꿔서 주소 `0x0`에 올린다.
처음 올리면 Wi-Fi와 키 설정이 모두 비어 있는 상태로 시작한다.

## 3. Wi-Fi와 키 입력 (휴대폰)

1. 기기가 `Xiaozhi-XXXX` Wi-Fi를 띄운다 → 휴대폰으로 연결 → 브라우저에서 `http://192.168.4.1`
2. **먼저 Advanced(고급) 탭**으로 간다.
   - Deepgram / DeepSeek / Google TTS 키 칸에 복사해 둔 키를 붙여 넣는다.
   - **Save**를 누른다. 각 칸 옆이 `(저장됨)`으로 바뀌면 된다.
3. 다시 첫 탭으로 와서 사용할 장소의 2.4GHz Wi-Fi를 고르고 비밀번호 입력 → **Connect**
4. 기기가 재부팅하고 바로 대화할 수 있는 상태가 된다. "Hi,ESP"로 깨운다.

키가 하나라도 비어 있으면 기기가 알아서 다시 설정 모드(`Xiaozhi-XXXX`)로 들어간다.
키를 바꾸고 싶을 때도 같은 화면에서 새 키만 넣고 Save 하면 된다. 비워 둔 칸은 기존 키를 유지한다.

## 4. 측정

`docs/FLASH_WEB.md`의 3번(Console에서 115200 연결)과 같은 방법으로 로그를 받는다. 짧은 질문 5번 정도.

로그에서 보는 줄

| 줄 | 뜻 |
|---|---|
| `LAT vad_end>stt=… stt>tts=… tts>audio=… vad_end>audio=…` | 대화 한 번의 구간별 시간(ms). 서버 펌웨어와 같은 형식이라 바로 비교된다 |
| `LAT llm_headers=… ms` | DeepSeek 요청 → 응답 시작 |
| `LAT llm_first_token=… ms` | DeepSeek 요청 → 첫 글자 |
| `LAT tts http=… total=… packets=… chars=…` | Google TTS 한 문장 합성 시간 |
| `Deepgram connected in … ms` | 음성 인식 연결에 걸린 시간 |

오류가 나면 `DirectProtocol` 태그가 붙은 줄에 이유가 찍힌다 (`DeepSeek status 401` 같은 형태).

---

## 아직 실제 기기로 확인하지 않은 것

빌드까지는 확인했고, 실제 동작은 첫 테스트에서 확인해야 한다.

- Deepgram 실시간 인식이 `nova-3` + 한국어(`ko`) 조합을 받아 주는지 (서버에서는 같은 조합을 일괄 인식으로 쓰고 있음)
- DeepSeek 모델 이름 `deepseek-flash` (서버 설정에서 가져온 값)
- Google 음성 이름 `ko-KR-Neural2-A`
- 음성 인식 연결 1개 + 답변 1개 + 음성 합성 1개, 암호화 연결 3개를 동시에 여는 메모리 상황

모델 이름이나 음성 이름이 틀리면 로그에 400/404 오류로 바로 드러난다. 그러면 기본값만 바꿔서 다시 빌드하면 된다.
