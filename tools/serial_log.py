#!/usr/bin/env python3
"""스택짱 시리얼 로그를 정해진 시간만큼 받아 화면과 파일에 남긴다.

Ctrl+C 없이 끝나므로 Claude Code가 직접 돌려서 결과를 읽기 좋다.

필요: pip install pyserial
사용법:
    python tools/serial_log.py COM5                      30초 받기
    python tools/serial_log.py COM5 --seconds 90         90초 받기
    python tools/serial_log.py COM5 --reset              기기를 재부팅시키고 부팅 로그부터
    python tools/serial_log.py COM5 --grep "LAT|Claude"  이 정규식에 맞는 줄만 화면에 (파일에는 전부)

로그 파일은 logs/serial-YYYYmmdd-HHMMSS.log 로 남는다.
포트를 다른 프로그램(웹 플래셔, Chrome 콘솔 탭)이 잡고 있으면 열리지 않는다.
"""
import argparse
import os
import re
import sys
import time

try:
    import serial
except ImportError:
    print("pyserial이 없습니다: pip install pyserial")
    sys.exit(1)

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("port")
    ap.add_argument("--seconds", type=float, default=30)
    ap.add_argument("--reset", action="store_true", help="RTS로 기기를 재부팅시킨 뒤 받기")
    ap.add_argument("--grep", help="화면에 보일 줄의 정규식")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(here, "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    out = os.path.join(log_dir, time.strftime("serial-%Y%m%d-%H%M%S.log"))
    pat = re.compile(args.grep) if args.grep else None

    ser = serial.Serial()
    ser.port = args.port
    ser.baudrate = 115200
    ser.timeout = 0.3
    # 포트를 열 때 DTR/RTS가 바뀌어 기기가 다운로드 모드로 들어가지 않게 먼저 내려 둔다
    ser.dtr = False
    ser.rts = False
    ser.open()
    if args.reset:
        ser.rts = True
        time.sleep(0.1)
        ser.rts = False

    end = time.time() + args.seconds
    buf = b""
    lines = 0
    with ser, open(out, "w", encoding="utf-8") as f:
        print(f"{args.port}에서 {args.seconds:.0f}초 수신 → {out}", flush=True)
        while time.time() < end:
            buf += ser.read(2048)
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                text = ANSI.sub("", line.decode("utf-8", "replace").rstrip("\r"))
                f.write(f"{time.strftime('%H:%M:%S')} {text}\n")
                lines += 1
                if pat is None or pat.search(text):
                    print(text, flush=True)
    print(f"끝: {lines}줄 저장 ({out})")


if __name__ == "__main__":
    main()
