# TrendHunter Operation Manual

이 문서는 TrendHunter 시스템의 설치, 초기화, 운영, 그리고 문제 해결을 위한 통합 가이드입니다.
(최종 업데이트: 2026-02-02)

---

## 1. 시스템 개요
TrendHunter는 KIS API를 기반으로 한국 주식 시장(KOSPI, KOSDAQ)의 전 종목 데이터를 수집하고, 정량적 전략(Minervini Trend, Dividend Growth 등)에 따라 유망 종목을 발굴하는 시스템입니다.

### 핵심 디렉토리 구조
*   `src/`: 소스 코드 (진입점 `run.py`가 이를 호출)
    *   `jobs/`: 데이터 수집 (API -> DB)
    *   `analysis/`: 데이터 분석 및 리포트 (DB -> Console)
    *   `db/`: DB 스키마 및 연결 관리
*   `TrendHunter/db/stock_info.db`: 메인 데이터베이스 (SQLite)

---

## 2. 초기화 (Reset & Init)
데이터베이스가 꼬였거나 처음부터 다시 시작해야 할 때 수행합니다.

```bash
# 1. 기존 DB 삭제
rm -f TrendHunter/db/stock_info.db

# 2. 필수 테이블 생성 및 기초 데이터 동기화
# (순서 중요: init -> sync -> themes -> views)
python3 run.py init      # 테이블(Schema) 생성
python3 run.py sync      # 종목 코드(Master) 동기화
python3 run.py themes    # 테마/업종 코드 동기화
python3 run.py views     # 분석용 View 생성
```

---

## 3. 데이터 수집 (Daily Routine)
데이터 수집은 시간이 오래 걸리므로 **백그라운드 실행(`nohup`)**을 권장합니다.
특히 입출력 에러 방지를 위해 `< /dev/null` 리다이렉션을 사용하는 것이 안정적입니다.

### 3.1 시세 수집 (가장 중요, 약 20~30분 소요)
전 종목의 일봉, 거래량, 이동평균선을 수집합니다.
```bash
nohup python3 -u run.py daily > fetch_daily.log 2>&1 < /dev/null &
# 진행 상황 확인: tail -f fetch_daily.log
```

### 3.2 보조 데이터 수집 (병렬 실행 가능)
시세 수집과 동시에 돌려도 됩니다. 리포트의 필터링(흑자 여부, 배당률, 수급)에 필수적입니다.

```bash
# 1. 펀더멘털 (PER, PBR, 영업이익 등)
nohup python3 -u run.py fundamentals > fetch_fund.log 2>&1 < /dev/null &

# 2. 배당 정보 (업종별 마이닝 - 시간이 좀 걸림)
nohup python3 -u run.py mine > fetch_div.log 2>&1 < /dev/null &

# 3. 수급 정보 (외국인/기관 매매동향 - 선택 사항)
nohup python3 -u run.py supply > fetch_supply.log 2>&1 < /dev/null &
```

---

## 4. 분석 및 리포트 (Reporting)
데이터 수집이 완료된 후 실행합니다.

### 4.1 RS 점수 계산 (필수)
상대 강도(Relative Strength) 점수를 계산하여 `daily_analysis` 테이블에 업데이트합니다.
```bash
python3 run.py rs
```

### 4.2 최종 리포트 출력
전설의 투자자(Minervini, O'Neil) 조건에 부합하는 종목을 선별하여 출력합니다.
```bash
python3 run.py screen
```

---

## 5. 트러블슈팅 (FAQ)

### Q. 리포트에 종목이 하나도 안 나와요.
1. **시세 데이터 부족**: `python run.py daily`가 정상적으로 완료되었는지 확인하세요. (최소 200일치 데이터 필요)
2. **필수 데이터 누락**: 펀더멘털(흑자 여부)이나 배당 데이터가 없으면 필터링될 수 있습니다. `run.py fundamentals`를 실행했는지 확인하세요.
3. **시장 상황**: 정말로 살 종목이 없을 수도 있습니다. (시장 하락장 등)

### Q. "Unknown" 이라고 뜨는 항목이 있어요.
*   **수급(Unknown)**: `run.py supply`를 실행하여 외국인/기관 데이터를 채워주세요.
*   **테마(Unknown)**: `run.py themes`를 실행하여 테마 정보를 동기화하세요.

### Q. 백그라운드 프로세스가 자꾸 죽어요 ("Bad file descriptor").
*   `nohup` 실행 시 `< /dev/null`을 끝에 붙여주세요. 파이썬이 백그라운드에서 표준 입력을 찾지 못해 죽는 현상입니다.
    *   `nohup python3 -u run.py ... > log 2>&1 < /dev/null &`

---

## 6. 개발 가이드 (For Developers)
*   **새로운 기능 추가**: `src/` 하위에 모듈을 만들고, `run.py`의 `COMMANDS`와 `runners` 딕셔너리에 등록하세요.
*   **날짜 로직**: KIS API 호출 시 조회 기간(`F_DT`, `T_DT`)을 하드코딩하지 말고 `datetime`을 사용하여 동적으로 처리하세요.
