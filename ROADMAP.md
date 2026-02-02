# TrendHunter Roadmap (2026)

## 1. 운영 목표 (Vision)
TrendHunter는 단순한 스크리닝 도구를 넘어, **시각적 데이터 분석(Dashboard)**과 **자동 매매(Auto-Trading)**가 결합된 종합 트레이딩 플랫폼을 지향합니다.

---

## 2. 기능 구현 현황 (Status)

| 카테고리 | 기능 | 상태 | 상세 내용 |
|:--- |:--- |:--- |:--- |
| **Data** | 마스터/테마 동기화 | ✅ | `run sync`, `run themes` |
| | 일봉/지표 수집 | ✅ | `run daily` (전 종목 2년치, 지표 자동 계산) |
| | 펀더멘털/배당/수급 | ✅ | `run fundamentals`, `run mine`, `run supply` |
| **Logic** | RS 점수 계산 | ✅ | `run rs` (시장 상대강도 0-99) |
| | 전략 리포팅 | ✅ | `run screen` (Track 1/2/EX 통합 리포트) |
| | 매매 계획 수립 | ✅ | `trade_plan` 테이블에 진입가/손절가 자동 저장 |
| **UI** | 웹 대시보드 | ⚠️ | React 프론트엔드(`dashboard/`) + FastAPI(`src/api.py`) 연동 (Beta) |
| **Trade** | 자동 매수 주문 | ❌ | `trade_plan` 기반 자동 주문 집행 모듈 개발 필요 |
| **Cloud** | GCP 배포 | ❌ | Cloud Scheduler + Cloud Run 구성 예정 |

---

## 3. 상세 로드맵 (Detailed Plans)

### 3.1 [Phase 1] 대시보드 고도화 (Current)
현재 CLI 기반의 리포트를 웹 브라우저에서 시각적으로 확인할 수 있도록 합니다.
*   **API 서버**: `src/api.py` (FastAPI) 기능 확장 (종목 상세, 차트 데이터 제공).
*   **UI 개발**: `dashboard/` (React+Vite)
    *   **Dashboard**: 오늘의 추천 종목(Track 1/2) 카드 뷰.
    *   **Chart**: TradingView 라이브러리 등을 활용한 VCP 패턴 시각화.
    *   **Interactive**: 사용자가 직접 차트에 지지/저항선을 긋거나 메모를 남기는 기능.

### 3.2 [Phase 2] 자동 매매 (Execution)
리포트에서 선정된 종목을 실제 계좌로 매매합니다.
*   **주문 집행기**: `run.py execute` 명령어 추가.
    *   장 시작 전: `trade_plan`의 `READY` 상태 주문을 KIS 서버에 예약 전송.
    *   장 중: 체결 확인 및 손절가 감시(Real-time Monitoring).
*   **알림 시스템**: 체결 내역 및 손절 발생 시 Telegram/Slack 알림.

### 3.3 [Phase 3] 클라우드 마이그레이션 (Deploy)
로컬 PC가 꺼져 있어도 시스템이 돌아가도록 합니다.
*   **DB**: SQLite -> Google Cloud SQL (PostgreSQL) 마이그레이션.
*   **Batch**: Google Cloud Scheduler로 `run daily` 자동화.
*   **Hosting**: Google Cloud Run으로 API 서버 및 대시보드 호스팅.

---

## 4. 참고 문서
*   **실행 가이드**: `MANUAL.md`
*   **기술 명세**: `FUNCTIONALITY_MAP.md`, `DB_DESIGN.md`