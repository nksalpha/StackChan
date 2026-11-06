# 작업 인계 메모

새 세션에서 이어갈 때 이 파일부터 읽고 시작한다.

마지막 갱신: 2026-11-05

## 목표

커스텀 펌웨어로 돌릴 때 음성 응답이 느리다. 원본(공장) 펌웨어 2.3.3 수준까지 응답 속도를 끌어올리는 것이 목표다.

## 장비와 구성

| 항목 | 내용 |
|---|---|
| 기기 | M5Stack CoreS3 (MAC `80:45:6b:4d:44:6c`) |
| 기기 현재 상태 | 원본 FW 2.3.3으로 복원해 둠 (비교 기준) |
| 커스텀 펌웨어 | `xiaozhi-stackchan-ko-full.bin` (11MB, sha256 확인 완료, 이 저장소에는 없음) |
| 서버 | TerraMaster F2-424 NAS, 컨테이너 `xiaozhi-esp32-server` |
| 서버 설정 | 한국어 / ASR Deepgram(비스트리밍) / TTS EdgeTTS / LLM DeepSeek / 기기 화이트리스트 사용 |

## 지금까지 확인한 것

- REPRODUCIBILITY.md를 검토했다. 서버 쪽 구성은 끝났고, 플래싱 절차(부록 A)는 그대로 따라 할 수 있는 수준이다. 다만 문서 자체에 손볼 곳이 8군데 있었다(MAC 노출, .env 연결이 끊긴 부분, 플래싱 방식 설명이 서로 맞지 않는 부분 등). 이 문서는 아직 저장소에 올라와 있지 않다.
- xiaozhi-esp32-server 기본 config.yaml로 설정 키를 대조했다. `server.auth.allowed_devices`, `prompt_template` 같은 키 이름과 ASR/TTS 제공자별 스트리밍 지원 여부를 확인했다.

## 느린 원인에 대한 가설 (미검증)

펌웨어 문제가 아니라 서버 쪽 처리 방식 차이일 가능성이 크다.

- 원본 펌웨어는 공식 서버에 붙어 있었을 가능성이 높다. 재현 문서에도 원본에서는 OTA URL을 바꾸는 경로를 찾지 못했다고 적혀 있다.
- 공식 서버는 ASR과 TTS를 스트리밍으로 처리한다. 지금 NAS 서버는 Deepgram을 REST로 호출해서, 말이 끝나고 나서야 인식 결과가 나온다.

## 새 기준 펌웨어 (2026-11-06)

이전 측정 계획은 접고, 새로 빌드한 커스텀 펌웨어를 기준으로 측정·개선한다.

- 이미지: `firmware/out/xiaozhi-stackchan-ko-full.bin` (11,124,461 B, sha256 `904e4def…7e04`)
- 빌드: ESP-IDF `9a97f6c`(release/v6.1), xiaozhi-esp32 `a73e9a7`, 보드 `m5stack/stackchan`(표정 유지), 언어 `ko-KR`, 버전 2.5.3
- OTA: `https://nams-nas.tail187299.ts.net/xiaozhi/ota/` (Funnel 유지. 서버와 기기 사용 장소가 다름)
- 패치: `firmware/patches/` — 구간 지연 로그(`LAT` 태그), 화면 대화 텍스트 숨김
- 재현: `bash firmware/build.sh` (부품 버전은 `firmware/dependencies.lock`으로 고정)
- 플래싱·측정: `docs/FLASH_WEB.md` (PC 브라우저, 기기는 사용자가 직접 가지고 있음)
- 클라우드 빌드 환경: 개인 환경 `StackChan` (Espressif 서버 3곳 허용)
- 서버 변경도 개선 범위에 포함. NAS 작업은 사용자가 NAS의 Claude Code로 실행하므로, 필요할 때 실행용 MD를 `docs/nas/`에 써서 넘긴다.

## 서버 없는 직접 연결 펌웨어 (2026-11-06)

사용자 결정으로 NAS 서버를 빼고 기기가 클라우드 API를 직접 부르는 구성을 시도 중. OpenAI Realtime은 비용 때문에 보류.

- 구성: Deepgram 실시간 인식(WebSocket, 말 끝 판정 포함) → DeepSeek 스트리밍 → Google Cloud TTS(OGG_OPUS)
- TTS 선택 경위: EdgeTTS는 Microsoft가 넣은 난독화 토큰을 역분석한 코드가 필요해서 기기 이식 제외. Azure 대신 사용자가 Google 선택
- 이미지: `firmware/out/xiaozhi-stackchan-ko-direct-full.bin`
- 코드: `firmware/patches/03-direct-cloud.patch`(DirectProtocol, Kconfig `DIRECT_CLOUD_MODE`), `04-wifi-connect-api-keys.patch`(설정 화면 고급 탭에 키 3개)
- 빌드: `bash firmware/build.sh direct`
- 사용·측정: `docs/DIRECT.md`
- 상태: 빌드 성공. 기기 테스트 전. 미확인 항목은 `docs/DIRECT.md` 끝에 정리

## 측정 도구 (2026-11-05 추가, 서버 로그용)

절차는 `docs/MEASURE.md`에 있다.

- `tools/serial_capture.py`: PC에서 시리얼 로그를 받아 기기가 붙는 서버 주소를 골라낸다.
- `tools/collect_server.sh`: NAS에서 `docker logs -t` 로그와 설정(키는 가림)을 모은다.
- `tools/latency_report.py`: 모은 로그로 턴마다 구간별 지연(ms)을 표로 낸다.

서버 로그 자체 시각은 초 단위라서 `docker logs -t`의 시각을 기준으로 쓴다. 기준 로그 문구는 xinnan-tech/xiaozhi-esp32-server main(2026-11-05 커밋 4f6e9ec)에서 확인했다.

확인 필요: 위 최신 서버 코드에는 Deepgram ASR 제공자가 없다. NAS 서버가 Deepgram을 어떻게 붙여 쓰고 있는지(포크, 직접 추가, OpenAI 호환 방식 등)를 수집한 설정 파일로 확인해야 한다.

## 다음에 할 일

1. 원본 FW가 어느 서버에 붙는지 확인한다. 원본 FW로 부팅한 상태에서 시리얼 로그(115200bps)를 보면 OTA/WebSocket 주소가 나온다. 가설이 맞는지는 여기서 갈린다.
2. NAS 서버에서 구간별 지연을 잰다. `docker logs -f xiaozhi-esp32-server`를 띄워 놓고 한 번 말을 걸어서 아래 세 구간의 시간을 본다.
   - 말 끝남(VAD 종료) → ASR 결과
   - ASR 결과 → LLM 첫 토큰
   - LLM 첫 문장 → 첫 TTS 오디오 전송
3. 가장 오래 걸리는 구간부터 고친다. 후보는 스트리밍 ASR로 교체, TTS 스트리밍 설정, LLM 응답을 문장 단위로 끊어 보내는 설정이다. 키 이름은 바꾸기 전에 공식 config.yaml에서 다시 확인한다.

## 작업 방식

- 실행 환경은 Claude 클라우드 세션이고, 이 저장소에 작업 결과를 남긴다.
- 클라우드에서는 기기(USB 시리얼)나 NAS에 직접 접근할 수 없다. 측정과 플래싱은 사용자가 직접 하고, 결과 로그를 `logs/` 폴더에 올리면 그걸 보고 분석한다.
- 작업은 사용자가 실행하라고 할 때만 한다.
