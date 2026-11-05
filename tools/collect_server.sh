#!/bin/sh
# NAS에서 실행: 서버 로그와 지연에 영향을 주는 설정을 한 번에 모은다.
# 사용법: sh collect_server.sh [로그 기간, 기본 15m]
# 결과: ./server-YYYYmmdd-HHMM/ 폴더 (API 키 등은 가려서 저장)

C=xiaozhi-esp32-server
SINCE=${1:-15m}
OUT=server-$(date +%Y%m%d-%H%M)
mkdir -p "$OUT"

docker logs -t --since "$SINCE" "$C" > "$OUT/server.log" 2>&1
echo "로그 저장: $OUT/server.log ($(wc -l < "$OUT/server.log") 줄)"

# 사용자 설정 파일. 키·토큰·비밀번호 값은 *** 로 바꿔서 저장한다.
CFG=/opt/xiaozhi-esp32-server/data/.config.yaml
if docker exec "$C" test -f "$CFG"; then
  docker exec "$C" cat "$CFG" \
    | sed -E 's/^([[:space:]]*[A-Za-z_]*(key|token|secret|password|access|appid|app_id)[A-Za-z_]*[[:space:]]*:[[:space:]]*).+$/\1"***"/' \
    > "$OUT/config.redacted.yaml"
  echo "설정 저장: $OUT/config.redacted.yaml (키 값은 가려짐, 올리기 전에 한 번 더 확인)"
else
  echo "설정 파일을 찾지 못함: $CFG (컨테이너 안 경로가 다르면 CFG 값을 고쳐서 다시 실행)"
fi

docker exec "$C" sh -c 'cd /opt/xiaozhi-esp32-server 2>/dev/null && git log -1 --format="%h %cd" 2>/dev/null' > "$OUT/server-version.txt" 2>&1
docker inspect --format '{{.Config.Image}} {{.Created}}' "$C" >> "$OUT/server-version.txt" 2>&1
echo "버전 정보: $OUT/server-version.txt"
