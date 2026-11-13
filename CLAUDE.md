# StackChan 작업 안내 (Claude Code용)

M5Stack 스택챤(CoreS3, ESP32-S3, 16MB 플래시, 8MB PSRAM)에 올리는 커스텀 xiaozhi 펌웨어 작업 저장소다. 사용자는 어린 조카가 쓸 대화 로봇으로 만들고 있다.

## 사용자와 일하는 방식

- 한국어로 답한다. 간결하게, 근거와 확인한 것/추측을 구분해서.
- 작업(코드 수정, 빌드, 플래싱, 커밋)은 사용자가 하라고 했을 때만 한다. 그 전에는 분석과 제안만.
- 문서는 사람이 쓴 것처럼 자연스럽게. 틀에 박힌 형식이나 번역투를 피한다.
- API 키를 채팅에 붙여 달라고 하지 않는다. 키는 기기 설정 화면에서 넣고 NVS(`direct` 네임스페이스)에만 있다. 펌웨어나 저장소에 넣지 않는다.
- 저장소는 비공개(MAC 주소, 설정 정보 포함). 외부 서비스에 그런 내용을 보내지 않는다.

## 먼저 읽을 것

- `HANDOFF.md`: 지금까지의 경과와 결정
- `docs/DIRECT.md`: 지금 쓰는 직접 연결 펌웨어(Deepgram → DeepSeek → Google TTS, 사진은 Claude Haiku 5.5)의 설정·로그 설명
- `docs/LOCAL.md`: PC 환경 준비

## 기기 다루기 (PC에 USB로 연결된 경우)

- 포트: 사용자가 알려 준 COM 번호. 모르면 `python -m serial.tools.list_ports`
- 로그: `python tools/serial_log.py COMx --reset --seconds 40` (끝나는 시간이 정해져 있어 그대로 실행 가능). 필요한 줄만 보려면 `--grep "LAT|Claude|Warmup|PY32"`
- 앱만 올리기: `python -m esptool --chip esp32s3 -p COMx -b 921600 write-flash 0x20000 firmware/out/xiaozhi-stackchan-ko-direct-app.bin`
- 전체 올리기: 같은 명령에서 `0x0 firmware/out/xiaozhi-stackchan-ko-direct-full.bin`. 합친 이미지가 NVS 자리까지 빈 값으로 덮어서 Wi-Fi·키·메모가 지워진다. 에셋(0x800000)이나 파티션이 바뀐 경우가 아니면 앱만 올린다.
- 절대 `erase-flash` 하지 않는다. Wi-Fi·API 키·기억 메모가 지워진다.
- esptool이 연결을 못 하면 사용자에게 리셋 버튼을 녹색 불이 켜질 때까지 길게 눌러 달라고 한다.
- 로그 포트와 플래싱 포트는 같다. 로그를 받는 중에는 플래싱이 안 된다.
- 로그 끝에 깨우기, 말하기 같은 사람 동작이 필요하면 받기 전에 사용자에게 무엇을 해 달라고 말해 둔다 ("Hi, ESP"로 깨우기 등).

## 펌웨어 소스와 빌드

- 소스는 이 저장소에 패치로만 있다: `firmware/patches/01~05`. 원본은 78/xiaozhi-esp32 `a73e9a7`, ESP-IDF release/v6.1 `9a97f6c`.
- 재현 빌드: 리눅스(또는 WSL2)에서 `bash firmware/build.sh direct` → 작업 폴더 `~/xiaozhi-build/xiaozhi-esp32`에 패치가 적용된 소스가 생긴다. 코드는 거기서 고치고, 고친 뒤에는 패치를 다시 만들어 저장소에 넣는다.
  - 03 패치(본체): 원본 커밋에 01·02를 적용한 상태와의 `git diff`. 포함 파일은 `main/application.cc, CMakeLists.txt, Kconfig.projbuild, idf_component.yml, protocols/direct_protocol.*, audio/audio_service.*, boards/m5stack/stackchan/{stackchan.cc,reactions.h}, boards/common/{camera.h,esp_video.h,esp_video.cc}`
  - 04(설정 화면), 05(HTTP keep-alive): 컴포넌트 캐시의 원본 `78__esp-wifi-connect` / `78__esp-ml307`과 `components/` 사본의 `diff -ru -x CHECKSUMS.json -x .component_hash`
- 빌드 산출물은 `firmware/out/`에 두고 `SHA256SUMS`를 갱신한다.
- 커밋 메시지는 한국어로, 무엇을 왜 바꿨는지.

## 지금 남은 일 (2026-11-13)

1. **좌우 LED가 계속 켜져 있음** (배터리 연결 후 처음 보고됨). 아직 원인 모름.
   - 펌웨어는 몸체 RGB LED(WS2812C 12개, PY32 보조 칩 I2C 0x6F가 구동, LED 설정 레지스터 0x24, LED RAM 0x30부터 2바이트씩 RGB565)에 아무것도 쓰지 않는다. 서보 전원(PY32 핀 0)만 켠다.
   - 몸체에는 별도의 전원 표시 LED도 있다.
   - 먼저 사용자에게 색·밝기, USB만 꽂았을 때도 켜지는지, 충전이 끝나면 바뀌는지 물어서 전원/충전 표시인지 RGB LED인지 가른다.
   - RGB LED라면 부팅 로그의 `PY32 ready (version …)`를 확인하고, 시작할 때 LED RAM을 0으로 쓰고 latch하는 코드를 넣어 꺼지는지 본다. 원하면 듣기/말하기 상태 표시로 확장.
2. **Claude 연결 미리 맺기 확인** (커밋 12c9fb5, 기기 미확인): 깨운 뒤 `Warmup Claude status=200`, 사진 질문 때 `Reusing existing connection to api.anthropic.com`, `LAT vad_end>audio`가 4.6초 → 약 3초로 줄었는지.
3. 이전부터 기기 확인이 남은 것: 터치 쓰다듬기·간지럼, 표정 1.5초 유지, 기억 메모 갱신 로그(`Memory updated in … ms`), I2C 수정 후 재부팅이 없는지.
4. 다음 후보: 기기 안 얼굴 감지(ESP-DL), 일반 대화를 Claude로 바꿀지 속도 비교.
