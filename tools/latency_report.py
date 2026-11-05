#!/usr/bin/env python3
"""xiaozhi-esp32-server 로그에서 대화 한 턴마다 구간별 지연을 뽑는다.

입력은 반드시 `docker logs -t` 출력이어야 한다. 서버 자체 로그 시각은
초 단위라서 쓸 수 없고, docker가 앞에 붙이는 나노초 시각을 기준으로 잰다.

사용법:
    docker logs -t --since 10m xiaozhi-esp32-server > server.log 2>&1
    python3 latency_report.py server.log

기준 로그 문구 (xinnan-tech/xiaozhi-esp32-server, 2026-11 main 기준):
    识别文本:            ASR 결과가 나온 시점
    总处理耗时:          ASR 처리 시간 (log_level DEBUG일 때만 찍힘)
    大模型收到用户消息:   LLM 요청 시작
    语音生成成功:         TTS 한 문장 합성 완료 (비스트리밍 TTS)
    发送第一段语音:       기기로 첫 음성 전송 시작
"""
import re
import sys
from datetime import datetime, timezone

TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d+))?Z\s")
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
ASR_TIME_RE = re.compile(r"总处理耗时:\s*([\d.]+)s")

MARKERS = {
    "asr_text": "识别文本:",
    "asr_time": "总处理耗时:",
    "llm_in": "大模型收到用户消息",
    "tts_ok": "语音生成成功",
    "first_audio": "发送第一段语音",
}


def parse_ts(line):
    m = TS_RE.match(line)
    if not m:
        return None
    base = datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    frac = (m.group(2) or "0")[:6].ljust(6, "0")
    return base.timestamp() + int(frac) / 1e6


def load_events(path):
    events = []
    no_ts = 0
    with open(path, encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = ANSI_RE.sub("", raw.rstrip("\n"))
            for name, key in MARKERS.items():
                if key in line:
                    ts = parse_ts(line)
                    if ts is None:
                        no_ts += 1
                        break
                    extra = None
                    if name == "asr_time":
                        m = ASR_TIME_RE.search(line)
                        extra = float(m.group(1)) if m else None
                    elif name == "asr_text":
                        extra = line.split(key, 1)[1].strip()
                    events.append((ts, name, extra))
                    break
    return events, no_ts


def build_turns(events):
    """'识别文本' 하나를 한 턴의 시작으로 보고 다음 '识别文本' 전까지 묶는다."""
    turns = []
    cur = None
    pending_asr_time = None
    for ts, name, extra in events:
        if name == "asr_time":
            # 识别文本 바로 뒤에 찍히므로 현재 턴에 붙인다
            if cur is not None and cur.get("asr_time") is None:
                cur["asr_time"] = extra
            else:
                pending_asr_time = extra
            continue
        if name == "asr_text":
            cur = {"text": extra, "asr_text": ts, "asr_time": pending_asr_time}
            pending_asr_time = None
            turns.append(cur)
            continue
        if cur is None:
            continue
        if name not in cur:
            cur[name] = ts
    return turns


def ms(a, b):
    if a is None or b is None:
        return None
    return (b - a) * 1000


def fmt(v):
    return f"{'-':>7}" if v is None else f"{v:7.0f}"


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    events, no_ts = load_events(sys.argv[1])
    if no_ts and not events:
        print("시각 정보가 없습니다. 로그를 `docker logs -t` 로 다시 받아 주세요.")
        sys.exit(1)
    turns = build_turns(events)
    if not turns:
        print("'识别文本' 줄을 찾지 못했습니다. 대화가 한 번이라도 있었던 구간인지 확인해 주세요.")
        sys.exit(1)

    print("단위: ms")
    print("A = ASR 처리 (DEBUG 로그일 때만)")
    print("B = ASR 결과 → LLM 요청")
    print("C = LLM 요청 → 첫 문장 TTS 완료 (LLM 첫 문장 생성 + TTS 합성)")
    print("D = 첫 문장 TTS 완료 → 기기로 첫 음성 전송")
    print("합계 = ASR 결과 → 첫 음성 전송 (A 제외)")
    print()
    print(f"{'#':>3} {'A':>7} {'B':>7} {'C':>7} {'D':>7} {'합계':>7}  인식 문장")
    rows = []
    for i, t in enumerate(turns, 1):
        a = t["asr_time"] * 1000 if t.get("asr_time") is not None else None
        b = ms(t["asr_text"], t.get("llm_in"))
        c = ms(t.get("llm_in"), t.get("tts_ok"))
        d = ms(t.get("tts_ok"), t.get("first_audio"))
        total = ms(t["asr_text"], t.get("first_audio"))
        rows.append((a, b, c, d, total))
        text = (t["text"] or "")[:30]
        print(f"{i:>3} {fmt(a)} {fmt(b)} {fmt(c)} {fmt(d)} {fmt(total)}  {text}")

    def avg(idx):
        vals = [r[idx] for r in rows if r[idx] is not None]
        return sum(vals) / len(vals) if vals else None

    print(f"{'평균':>3} {fmt(avg(0))} {fmt(avg(1))} {fmt(avg(2))} {fmt(avg(3))} {fmt(avg(4))}")
    print()
    print("참고: 말이 끝난 뒤 VAD가 끝을 판정하기까지 걸리는 시간(min_silence_duration_ms)은")
    print("로그로 잴 수 없어서 위 표에 없습니다. 설정값을 그대로 더해서 보면 됩니다.")


if __name__ == "__main__":
    main()
