#!/usr/bin/env python3
"""CoreS3 시리얼 로그를 받아 저장하면서, 기기가 접속하는 서버 주소를 골라 보여준다.

필요: pip install pyserial
사용법:
    python3 serial_capture.py COM5            (Windows)
    python3 serial_capture.py /dev/ttyACM0    (Linux)
    python3 serial_capture.py /dev/cu.usbmodem101   (macOS)

실행한 뒤 기기 리셋 버튼을 한 번 누르면 부팅 로그부터 잡힌다.
Ctrl+C로 끝내면 serial-YYYYmmdd-HHMMSS.log 파일이 남는다.

골라내는 문구 (78/xiaozhi-esp32 펌웨어 기준, 2.3.3도 같은 계열로 예상):
    Ota: Current version            펌웨어 버전
    Connecting to websocket server  WebSocket 서버 주소
    Connecting to endpoint          MQTT 서버 주소 (공식 서버는 보통 MQTT+UDP)
"""
import re
import sys
import time

try:
    import serial
except ImportError:
    print("pyserial이 없습니다: pip install pyserial")
    sys.exit(1)

KEYS = re.compile(
    r"Current version|Connecting to websocket server|Connecting to endpoint|"
    r"Resolved MQTT host|ota_url|https?://|wss?://",
    re.I,
)
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    port = sys.argv[1]
    out = time.strftime("serial-%Y%m%d-%H%M%S.log")
    found = []
    with serial.Serial(port, 115200, timeout=0.5) as ser, open(out, "w", encoding="utf-8") as f:
        print(f"{port} 수신 중 → {out}  (기기 리셋 후 대기, Ctrl+C로 종료)")
        try:
            buf = b""
            while True:
                buf += ser.read(1024)
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    text = ANSI.sub("", line.decode("utf-8", "replace").rstrip("\r"))
                    stamp = time.strftime("%H:%M:%S")
                    f.write(f"{stamp} {text}\n")
                    f.flush()
                    if KEYS.search(text):
                        found.append(text)
                        print(f">> {text}")
        except KeyboardInterrupt:
            pass
    print()
    print("=== 서버 관련 줄 ===")
    for t in found or ["(찾지 못함: 리셋 후 Wi-Fi 연결까지 기다렸는지 확인)"]:
        print(t)


if __name__ == "__main__":
    main()
