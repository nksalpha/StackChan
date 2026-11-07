#!/bin/bash
# 커스텀 펌웨어 재현 빌드 스크립트 (Linux x86_64)
# 사용법: bash firmware/build.sh [server|direct] [작업폴더, 기본 ~/xiaozhi-build]
#   server: NAS xiaozhi-server에 붙는 펌웨어 → firmware/out/xiaozhi-stackchan-ko-full.bin
#   direct: 서버 없이 Deepgram/DeepSeek/Google TTS를 직접 부르는 펌웨어
#           → firmware/out/xiaozhi-stackchan-ko-direct-full.bin
set -euo pipefail

VARIANT=${1:-server}
REPO=$(cd "$(dirname "$0")/.." && pwd)
WORK=${2:-$HOME/xiaozhi-build}
IDF_COMMIT=9a97f6c54ec638111ce55cd36581b3c192f15207   # release/v6.1
FW_COMMIT=a73e9a7e266e3196d1368ba46c30bee0d81f0a64    # 78/xiaozhi-esp32
OTA_URL="https://nams-nas.tail187299.ts.net/xiaozhi/ota/"
mkdir -p "$WORK"; cd "$WORK"

if [ ! -d esp-idf ]; then
  git clone -b release/v6.1 https://github.com/espressif/esp-idf.git esp-idf
  git -C esp-idf checkout "$IDF_COMMIT"
  git -C esp-idf submodule update --init --recursive --depth 1
fi
# 툴체인은 GitHub 대신 Espressif 미러에서 받는다
export IDF_GITHUB_ASSETS="dl.espressif.com/github_assets"
./esp-idf/install.sh esp32s3
. ./esp-idf/export.sh

if [ ! -d xiaozhi-esp32 ]; then
  git clone https://github.com/78/xiaozhi-esp32.git xiaozhi-esp32
fi
cd xiaozhi-esp32
git checkout -f "$FW_COMMIT"
git clean -fdxq main components managed_components
git apply "$REPO/firmware/patches/01-latency-probe.patch"
git apply "$REPO/firmware/patches/02-hide-chat-text.patch"
# 부품 버전을 이 저장소에 기록된 것으로 고정
cp "$REPO/firmware/dependencies.lock" dependencies.lock

python ./scripts/build.py m5stack/stackchan --language ko-KR
# build.py가 sdkconfig를 다시 쓰므로 OTA 주소는 그 뒤에 넣고 한 번 더 빌드한다
sed -i "s|^CONFIG_OTA_URL=.*|CONFIG_OTA_URL=\"$OTA_URL\"|" sdkconfig
grep -q "^CONFIG_OTA_URL=\"$OTA_URL\"" sdkconfig

OUT_NAME=xiaozhi-stackchan-ko-full.bin
if [ "$VARIANT" = "direct" ]; then
  # Wi-Fi 설정 부품을 프로젝트 안으로 복사해 API 키 입력 칸을 추가한다
  mkdir -p components
  rm -rf components/esp-wifi-connect
  cp -r managed_components/78__esp-wifi-connect components/esp-wifi-connect
  rm -f components/esp-wifi-connect/CHECKSUMS.json components/esp-wifi-connect/.component_hash
  (cd components/esp-wifi-connect && patch -p1 < "$REPO/firmware/patches/04-wifi-connect-api-keys.patch")
  # HTTP 부품: HTTP/1.1 기본 keep-alive 처리 (Google TTS 연결 재사용)
  rm -rf components/esp-ml307
  cp -r managed_components/78__esp-ml307 components/esp-ml307
  rm -f components/esp-ml307/CHECKSUMS.json components/esp-ml307/.component_hash
  (cd components/esp-ml307 && patch -p1 < "$REPO/firmware/patches/05-ml307-http11-keepalive.patch")
  git apply "$REPO/firmware/patches/03-direct-cloud.patch"
  sed -i '/CONFIG_DIRECT_CLOUD_MODE/d' sdkconfig
  echo 'CONFIG_DIRECT_CLOUD_MODE=y' >> sdkconfig
  # 원음(초당 32KB)을 해외 서버로 실시간 전송하려면 기본 TCP 송신 버퍼(5.7KB)로는 모자라다
  sed -i 's/^CONFIG_LWIP_TCP_SND_BUF_DEFAULT=.*/CONFIG_LWIP_TCP_SND_BUF_DEFAULT=16384/' sdkconfig
  OUT_NAME=xiaozhi-stackchan-ko-direct-full.bin
fi
idf.py build

mkdir -p "$REPO/firmware/out"
cd build
esptool --chip esp32s3 merge-bin -o "$REPO/firmware/out/$OUT_NAME" \
  --flash-mode dio --flash-size 16MB --flash-freq 80m \
  0x0 bootloader/bootloader.bin \
  0x8000 partition_table/partition-table.bin \
  0xd000 ota_data_initial.bin \
  0x20000 xiaozhi.bin \
  0x800000 configured_assets.bin
sha256sum "$REPO/firmware/out/$OUT_NAME"
