# 🚀 TrendHunter (트렌드헌터)

**TrendHunter**는 한국투자증권(KIS) API를 활용하여 전설적인 시장 주도주 매매 전략(Jesse Livermore, William O'Neil, Mark Minervini)을 자동화하고, 고배당 전략을 결합한 통합 퀀트 매매 시스템입니다.

---

## 📋 목차
1. [시스템 요구사항](#-시스템-요구사항)
2. [설치 및 환경 설정](#-설치-및-환경-설정)
3. [핵심 키 설정 가이드](#-핵심-키-설정-가이드)
4. [시스템 초기화 및 동기화](#-시스템-초기화-및-동기화)
5. [운영 및 실행](#-운영-및-실행)
6. [Tailscale 기반 원격 서버 설정 (Mac/Windows)](#-tailscale-기반-원격-서버-설정-macwindows)

---

## 💻 시스템 요구사항
- **Python**: 3.11 (권장)
- **Node.js**: 18.x 이상 (대시보드 빌드용)
- **OS**: macOS (Apple Silicon 최적화) 또는 Windows 10/11
- **Network**: Tailscale (원격 접속용)

---

## 🛠 설치 및 환경 설정

### 1. 리포지토리 클론 및 가상환경 설정
```bash
git clone https://github.com/your-repo/trade.git
cd trade

# 서브모듈 초기화 (프론트엔드 소스 로드)
git submodule update --init --recursive

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# .\venv\Scripts\activate  # Windows
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
cd trade-front
npm install
npm run build
cd ..
```

---

## 🔑 핵심 키 설정 가이드

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 아래 내용을 입력합니다.

### 1. 한국투자증권(KIS) API 설정
- [KIS Developers](https://apicenter.koreainvestment.com/)에서 앱을 신청하여 키를 발급받으세요.
```env
APP_KEY="발급받은 APP KEY"
APP_SECRET="발급받은 APP SECRET"
CANO="계좌번호 8자리"
ACNT_PRDT_CD="01" # 계좌상품코드 (보통 01)
MODE="real" # 실전투자: real, 모의투자: vts
```

### 2. 텔레그램 알림 봇 설정
- `@BotFather`를 통해 봇을 생성하고 토큰을 받으세요.
- `@userinfobot` 등을 통해 자신의 `CHAT_ID`를 확인하세요.
```env
TELEGRAM_TOKEN="봇 토큰"
TELEGRAM_CHAT_ID="본인의 CHAT ID"
```

---

## 🔄 시스템 초기화 및 동기화

최초 실행 시 데이터베이스 구조를 만들고 마스터 데이터를 동기화해야 합니다.

```bash
# 1. DB 및 테이블 생성
python3 run.py init

# 2. 전 종목 마스터 데이터 동기화
python3 run.py sync

# 3. 테마 및 뷰 생성
python3 run.py themes
python3 run.py views

# 4. (매일 장 종료 후) 일일 데이터 수집 및 분석
python3 run.py daily
```

---

## 🏃 운영 및 실행

### 1. 프론트엔드 빌드 (UI 업데이트 시)
프론트엔드 코드를 수정했거나 처음 실행할 때, 정적 파일 생성을 위해 빌드가 필요합니다.
```bash
cd trade-front
npm install
npm run build
cd ..
```

### 2. 통합 서버 실행 (API + 대시보드)
빌드된 프론트엔드 파일과 백엔드 API를 하나의 포트(7777)에서 통합 실행합니다.
```bash
python3 run_server.py
```

### 3. 자동 매매 봇 실행
실시간 시세 감시 및 주문을 수행하는 봇을 별도의 프로세스로 실행합니다.
```bash
bash run_bot.sh
```

---

## 🌐 Tailscale 기반 원격 서버 설정 (Mac/Windows)

로컬에서 가동 중인 TrendHunter 서버를 외부(모바일 등)에서 안전하게 접속하기 위해 Tailscale을 사용합니다.

### 1. 공통 설정
1. [Tailscale](https://tailscale.com/) 회원가입 및 기기 로그인.
2. 서버가 가동되는 PC(Mac/Windows)와 접속할 기기(iPhone/Android 등) 모두에 Tailscale 앱 설치.

### 2. Mac에서 서버 설정
- 별도의 설정 없이 Tailscale 가동 후, 할당된 **Tailscale IP**를 확인하세요.
- `http://[Tailscale-IP]:7777`로 접속 가능합니다.

### 3. Windows에서 서버 설정
- **방화벽 허용**: 7777 포트에 대한 인바운드 규칙을 추가해야 합니다.
  1. `제어판 > 시스템 및 보안 > Windows Defender 방화벽 > 고급 설정`
  2. `인바운드 규칙 > 새 규칙 > 포트 > TCP > 7777` 허용
- **서버 실행**: `.\venv\Scripts\python src\api\main.py`

### 4. 접속 확인
- 모바일 또는 외부 기기에서 Tailscale 앱을 켜고 연결을 확인합니다.
- 브라우저 주소창에 `http://100.x.y.z:7777` 형식을 입력하여 대시보드에 진입합니다.

---

## 📂 프로젝트 구조
- `src/`: 백엔드 및 퀀트 엔진 로직
- `trade-front/`: React 기반 대시보드 프론트엔드
- `TrendHunter/`: DB 및 마스터 파일 보관소
- `docs/`: 기술 명세 및 가이드 문서

---
**최종 지침**: "데이터가 없으면 매매는 도박이다." 매일 장 종료 후 `run.py daily`를 통해 데이터를 최신화하십시오.
