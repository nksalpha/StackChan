# 펌웨어 올리기와 측정 (PC 브라우저)

설치할 프로그램은 없다. PC의 Chrome이나 Edge만 있으면 된다. Safari와 Firefox는 USB 시리얼을 지원하지 않는다.

준비물
- 펌웨어 파일: 저장소의 `firmware/out/xiaozhi-stackchan-ko-full.bin`
  - GitHub에서 파일을 열고 오른쪽 위 다운로드 버튼(↓)을 눌러 PC에 받는다.
  - 받은 뒤 크기와 sha256이 `firmware/out/SHA256SUMS`와 같은지 보면 더 확실하다.
- USB-C **데이터** 케이블. 충전 전용 케이블은 기기가 인식되지 않는다.

---

## 1. 플래싱

1. CoreS3를 PC에 꽂는다.
2. Chrome에서 https://espressif.github.io/esptool-js/ 를 연다.
3. **Program** 영역에서
   - Baudrate: `921600`
   - **Connect** → 목록에서 `USB JTAG/serial debug unit` 선택 → 연결
   - 연결이 안 되면: 기기 하단 RESET 버튼을 2~3초 눌러 초록 LED가 켜지면 놓고 다시 Connect
4. Flash Address `0x0`, 파일 선택에서 받은 `.bin` 지정
5. **Program** 클릭. 1~2분 걸리고, 끝나면 로그 끝에 `Hash of data verified`가 나온다.
6. **Disconnect** 누르고 기기 RESET 버튼을 한 번 짧게 누른다.

처음 원본 FW에서 넘어올 때는 Wi-Fi 설정이 지워진다. 파티션 배치가 달라서 통짜로 쓰기 때문이고, 고장이 아니다.

## 2. Wi-Fi 다시 잡기 (처음 한 번)

1. 기기가 `Xiaozhi-XXXX` Wi-Fi를 띄운다.
2. 휴대폰으로 그 Wi-Fi에 연결한다. "인터넷 없음"이 뜨면 "계속 연결". 모바일 데이터는 잠깐 꺼 두는 게 좋다.
3. 브라우저에서 `http://192.168.4.1` → 사용할 장소의 **2.4GHz** Wi-Fi 입력 → 저장
4. 기기가 재부팅되고 서버에 붙는다. OTA 주소는 펌웨어에 들어 있어 입력할 필요 없다.

## 3. 측정

1. 같은 esptool-js 페이지 아래쪽 **Console** 영역에서 Baudrate `115200` → **Start** → 포트 선택
2. "Hi,ESP"로 깨운 다음, 짧은 질문을 5번 정도 한다. 비슷한 길이로 한다. (예: "오늘 기분 어때?")
3. 콘솔 내용을 전부 선택해서 복사한 뒤, 텍스트 파일로 저장해 저장소 `logs/` 폴더에 올린다.
   - 올리는 방법: GitHub 저장소 → `logs` 폴더 → **Add file → Upload files** → **Commit changes**
   - 대화창에 그대로 붙여넣어도 된다.

로그에서 보는 줄은 이렇게 생겼다. 대화 한 번에 한 줄씩 나온다.

```
I (123456) LAT: LAT vad_end>stt=812 stt>tts=640 tts>audio=95 vad_end>audio=1547
```

| 값 | 뜻 (ms) |
|---|---|
| `vad_end>stt` | 말을 멈춘 뒤 → 인식 결과가 기기에 도착. 서버 무음 판정 + 음성 인식(Deepgram) + 왕복 |
| `stt>tts` | 인식 결과 → 서버가 답변 음성 시작을 알림. 답변 생성(DeepSeek) 첫 문장 + 음성 합성 |
| `tts>audio` | 음성 시작 알림 → 첫 음성 데이터 도착 |
| `vad_end>audio` | 말을 멈춘 뒤 → 첫 음성 데이터 도착. **체감 지연에 가장 가까운 값** |

`-1`이 찍힌 칸은 그 시점을 못 잡은 경우다. 기기 VAD가 말 끝을 못 잡았을 때 생길 수 있다.

## 4. 원본으로 되돌리기

NAS의 백업 `/Volume1/docker/xiaozhi-fw/backup/stock-core-s3-20261105.bin`을 PC로 가져와서, 같은 방법으로 주소 `0x0`에 올린다.
