# 응답 지연 측정 절차

두 가지를 확인한다.

1. 원본 FW 2.3.3이 어느 서버에 붙어 있는지 (PC에서 시리얼 로그)
2. NAS 서버에서 어느 구간이 오래 걸리는지 (NAS에서 docker 로그)

결과 파일은 `logs/` 폴더에 올리면 된다. 올리는 방법은 맨 아래에 있다.

---

## 1. 원본 FW 접속 서버 확인 (PC)

준비: Python 3, `pip install pyserial`, USB-C 데이터 케이블

1. CoreS3를 PC에 연결하고 포트 이름을 확인한다.
   - Windows: 장치 관리자 → 포트(COM & LPT) → `USB 직렬 장치 (COMx)`
   - macOS: `ls /dev/cu.usbmodem*`
   - Linux: `ls /dev/ttyACM*`
2. `tools/serial_capture.py`를 받아서 실행한다.
   ```
   python3 serial_capture.py COM5
   ```
3. 기기 리셋 버튼을 한 번 누르고, Wi-Fi에 붙어서 대기 화면이 나올 때까지 기다린 다음 Ctrl+C.
4. 화면 끝에 `=== 서버 관련 줄 ===` 아래로 찍힌 내용과 `serial-날짜.log` 파일을 올린다.

결과 읽는 법

| 찍힌 줄 | 의미 |
|---|---|
| `Connecting to endpoint ...` | MQTT로 접속. 공식 서버(xiaozhi.me)는 보통 이 방식 |
| `Connecting to websocket server: ws://192.168...` | 집 안 서버(NAS)로 접속 |
| `Connecting to websocket server: wss://...` 외부 주소 | 공식 서버나 다른 외부 서버 |

원본이 공식 서버에 붙어 있었다면, 빠른 이유는 펌웨어가 아니라 서버 쪽에 있다는 뜻이 된다.

참고: 시리얼 포트를 다른 프로그램(Arduino IDE, 웹 플래셔 등)이 잡고 있으면 열리지 않는다. 그런 창은 먼저 닫는다.

---

## 2. NAS 서버 구간별 지연 측정

이 단계는 커스텀 FW로 NAS 서버에 붙은 상태에서 한다. 원본 FW로는 NAS 서버에 붙지 않기 때문이다.

### 2-1. (선택) ASR 처리 시간까지 보려면 DEBUG 로그 켜기

ASR 처리 시간은 DEBUG 레벨에서만 찍힌다. NAS의 `data/.config.yaml`에 아래를 넣고 컨테이너를 재시작한다. 측정이 끝나면 지우거나 `INFO`로 되돌린다.

```yaml
log:
  log_level: DEBUG
```

### 2-2. 대화하고 로그 모으기

1. 기기에 짧은 질문을 5번 정도 한다. 매번 비슷한 길이로 한다. (예: "오늘 기분 어때?")
2. NAS에 SSH로 접속해서 `tools/collect_server.sh`를 실행한다.
   ```
   sh collect_server.sh 15m
   ```
   최근 15분 로그와 설정 파일을 `server-날짜/` 폴더에 모은다. 설정 파일 안의 API 키·토큰 값은 `***`로 가려서 저장하지만, 올리기 전에 한 번 열어서 남은 키가 없는지 확인한다.
3. 바로 결과를 보고 싶으면 NAS나 PC에서:
   ```
   python3 latency_report.py server-날짜/server.log
   ```

### 결과 표 읽는 법

| 칸 | 구간 | 큰 경우 의심할 곳 |
|---|---|---|
| A | ASR 처리 | 비스트리밍 ASR. 말이 끝난 뒤에야 전송·인식이 시작됨 |
| B | ASR 결과 → LLM 요청 | 의도 인식(Intent) 단계, 메모리 처리 |
| C | LLM 요청 → 첫 문장 TTS 완료 | LLM 첫 응답 속도 + TTS 합성 시간 |
| D | TTS 완료 → 첫 음성 전송 | 오디오 변환, 전송 대기 |

표에 안 나오는 시간이 하나 더 있다. 말을 멈춘 뒤 서버가 "말이 끝났다"고 판정하기까지 기다리는 시간으로, `VAD.SileroVAD.min_silence_duration_ms` 값이다. 공식 기본 config.yaml은 200ms인데, 이 값이 설정에 아예 없으면 코드 기본값 1000ms가 적용된다. 수집된 설정 파일에서 같이 확인한다.

C가 크게 나오면 LLM과 TTS를 따로 나눠 봐야 한다. 지금 로그로는 둘이 붙어서 나오므로, 그 경우 다음 단계에서 따로 재는 방법을 정한다.

---

## 결과 올리는 방법

GitHub 웹에서 올리면 된다.

1. `github.com/nksalpha/StackChan` → `logs` 폴더로 이동
2. **Add file → Upload files**
3. 파일을 끌어다 놓고 **Commit changes**

올린 뒤 새 세션이나 이 세션에 "logs 올렸어"라고 하면 분석한다.
