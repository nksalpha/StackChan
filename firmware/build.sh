#!/bin/bash
# 커스텀 펌웨어 재현 빌드 스크립트 (Linux x86_64)
# 사용법: bash firmware/build.sh [작업폴더, 기본 ~/xiaozhi-build]
# 결과: firmware/out/xiaozhi-stackchan-ko-full.bin (0x0 통짜 이미지)
set -euo pipefail

REPO=$(cd "$(dirname "$0")/.." && pwd)
WORK=${1:-$HOME/xiaozhi-build}
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
git clean -fdq main
for p in "$REPO"/firmware/patches/*.patch; do git apply "$p"; done
# 부품 버전을 이 저장소에 기록된 것으로 고정
cp "$REPO/firmware/dependencies.lock" dependencies.lock

python ./scripts/build.py m5stack/stackchan --language ko-KR
# build.py가 sdkconfig를 다시 쓰므로 OTA 주소는 그 뒤에 넣고 한 번 더 빌드한다
sed -i "s|^CONFIG_OTA_URL=.*|CONFIG_OTA_URL=\"$OTA_URL\"|" sdkconfig
grep -q "^CONFIG_OTA_URL=\"$OTA_URL\"" sdkconfig
idf.py build

mkdir -p "$REPO/firmware/out"
cd build
esptool --chip esp32s3 merge-bin -o "$REPO/firmware/out/xiaozhi-stackchan-ko-full.bin" \
  --flash-mode dio --flash-size 16MB --flash-freq 80m \
  0x0 bootloader/bootloader.bin \
  0x8000 partition_table/partition-table.bin \
  0xd000 ota_data_initial.bin \
  0x20000 xiaozhi.bin \
  0x800000 configured_assets.bin
sha256sum "$REPO/firmware/out/xiaozhi-stackchan-ko-full.bin"
