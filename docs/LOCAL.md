# 내 PC의 Claude Code에서 이어서 하기

클라우드 세션은 기기에 USB로 닿을 수 없다. 기기를 PC에 꽂고 PC에서 Claude Code를 돌리면, Claude가 직접 펌웨어를 올리고 로그를 읽으면서 확인할 수 있다.

## 1. 한 번만 준비 (Windows)

1. 설치
   - Git: https://git-scm.com/download/win
   - Python 3.11 이상: https://www.python.org/downloads/ (설치 첫 화면에서 "Add python.exe to PATH" 체크)
   - Claude Code: https://code.claude.com/docs/en/setup 의 Windows 안내대로
2. PowerShell을 열고 저장소 받기
   ```
   cd $HOME
   git clone https://github.com/nksalpha/StackChan.git
   cd StackChan
   ```
   비공개 저장소라 처음에 GitHub 로그인 창이 뜬다. 로그인하면 된다.
3. 도구 설치
   ```
   pip install esptool pyserial
   ```

## 2. 기기 연결

1. USB-C 케이블로 PC에 꽂는다 (충전 전용 케이블은 안 된다).
2. 장치 관리자 → 포트(COM & LPT)에 `USB 직렬 장치 (COM5)` 같은 항목이 보이면 된다. 번호를 기억해 둔다.
3. Chrome 웹 플래셔나 콘솔 탭은 닫는다. 포트는 한 프로그램만 쓸 수 있다.

## 3. Claude Code 시작

```
cd $HOME\StackChan
claude
```

첫마디는 이렇게 하면 된다.

> CLAUDE.md 읽고 이어서 하자. 기기는 COM5에 연결했어.

Claude가 명령을 실행할 때마다 허락을 묻는다. 펌웨어 올리기(`esptool`)와 로그 받기(`tools/serial_log.py`)는 허락해 주면 된다.

## 참고: 직접 해 볼 때 쓰는 명령

로그 30초 받기 (기기 재부팅 포함)
```
python tools/serial_log.py COM5 --reset --seconds 30
```

앱 부분만 올리기 (설정·키는 그대로 남는다)
```
python -m esptool --chip esp32s3 -p COM5 -b 921600 write-flash 0x20000 firmware/out/xiaozhi-stackchan-ko-direct-app.bin
```

연결이 안 되면 리셋 버튼을 녹색 불이 켜질 때까지 길게 눌러 다운로드 모드로 넣고 다시 실행한다. 올린 뒤에는 리셋 버튼을 한 번 누른다.

`erase-flash`는 쓰지 않는다. Wi-Fi, API 키, 기억 메모가 모두 지워진다.

## 펌웨어 빌드는 어디서?

빌드(`firmware/build.sh`)는 리눅스용이고 ESP-IDF 설치에 수 GB가 든다. PC에서 하려면 WSL2(Ubuntu)를 깔고 그 안에서 `bash firmware/build.sh direct`를 돌린다. 만들어진 파일은 `firmware/out/`에 생기고, 플래싱은 위 명령처럼 Windows 쪽에서 한다.

PC에 빌드 환경을 꾸리기 번거로우면 코드 수정과 빌드는 지금처럼 클라우드 세션에서 하고, PC의 Claude Code는 `git pull` → 플래싱 → 로그 확인만 맡겨도 된다.
