# 운영 로드맵 & GCP 배포

## 1. 목표 운영 흐름

### 1.1 최초 1회
1. **마스터 다운로드** — KOSPI/KOSDAQ MST, DWS 업종/테마 ZIP
2. **마이그** — DB 적재 (master_info, sectors_themes)
3. **매일 종가 추가** — 일봉 수집 (fetch_daily_price) → daily_analysis
4. **빈데이터 계산** — RS·지표·배당 등 계산 (calc_rs_score, recalc_indicators, 배당 수집/태깅)
5. **레포팅** — Track1/Track2 리포트 (screen_market)

### 1.2 일일 배치 (매일)
- 종가 추가 → 지표·RS 계산 → (선택) 배당 갱신 → 레포팅

### 1.3 관심종목 + 실시간 감시 (추가 목표)
- **관심종목 등록** — 레포트/스크리닝 결과에서 선택한 종목을 DB 또는 설정에 등록
- **실시간 감시** — 관심종목에 대해 실시간 시세·조건 감시 (VCP 돌파, 볼륨 급증 등)
- **매수 타이밍 안내** — 조건 충족 시 알림/안내 (앱 푸시, 이메일, 슬랙 등)

---

## 2. 현재 구현 상태

| 단계 | 상태 | 비고 |
|------|------|------|
| 마스터 다운로드·마이그 | ✅ | run sync, run themes |
| 매일 종가 추가 | ✅ | run daily |
| 빈데이터 계산 | ✅ | run rs, run recalc, 배당 수집/태깅 |
| 레포팅 | ✅ | run screen |
| 관심종목 등록 | ❌ | 스키마·UI/설정 필요 |
| 실시간 감시 | ❌ | KIS 웹소켓 또는 폴링 |
| 매수 타이밍 안내 | ❌ | 알림 채널 연동 |

---

## 3. GCP 배포 검토

### 3.1 올릴 것
- **일일 배치:** 마스터·종가·지표·레포트까지 매일 정해진 시간에 실행
- **(추후) 실시간 감시:** 관심종목 실시간 감시 + 매수 타이밍 안내

### 3.2 GCP 구성 후보
| 용도 | 후보 | 비고 |
|------|------|------|
| 일일 배치 스케줄 | **Cloud Scheduler** + **Cloud Functions** 또는 **Cloud Run Jobs** | cron으로 run daily → rs → screen 등 순차 실행 |
| DB | **Cloud SQL**(MySQL/PostgreSQL) 또는 **SQLite 파일 → GCS** | 현재 SQLite 유지 시 VM/Cloud Run에서 볼륨 마운트 또는 GCS 동기화 |
| 실시간 감시 | **Cloud Run**(상시 1개 인스턴스) 또는 **GCE VM** | 웹소켓 장기 연결 시 VM이 유리 |
| 시크릿 | **Secret Manager** | APP_KEY, APP_SECRET, kis_token 등 |
| 알림 | **Cloud Pub/Sub** + **Cloud Functions** 또는 슬랙/이메일 API | 매수 타이밍 안내 연동 |

### 3.3 배포 순서 제안
1. **1단계:** 일일 배치만 GCP에 올리기  
   - Cloud Run Job(또는 Function)으로 `run daily` → `run rs` → `run screen` 스크립트 실행  
   - Cloud Scheduler로 매일 장 마감 후 호출  
   - DB는 SQLite 파일을 Cloud Storage에 두고 Job에서 다운로드 후 실행·업로드, 또는 소규모면 Cloud SQL로 이전
2. **2단계:** 관심종목 테이블·등록 API(또는 설정 파일) 추가
3. **3단계:** 실시간 감시 서비스 추가 → 매수 타이밍 시 알림

---

## 4. 참고
- 실행 방법: `MANUAL.md`, `python run.py`
- 기능 상세: `FUNCTIONALITY_MAP.md`
