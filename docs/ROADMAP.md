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
| **UI** | 웹 대시보드 | ✅ | React 프론트엔드(`trade-front/`) + FastAPI 연동 (v9.5 최적화 완료) |
| **Trade** | 자동 매수 주문 | ⚠️ | `trade_bot.py` 구현 완료, 현재 실계좌 검증 및 안전 모드 테스트 중 |
| **Cloud** | GCP 배포 | ❌ | Cloud Scheduler + Cloud Run 구성 예정 |

---

## 3. 상세 로드맵 (Detailed Plans)

### 3.1 [Phase 1] 대시보드 고도화 (Complete - v9.5)
현재 CLI 기반의 리포트를 웹 브라우저에서 시각적으로 확인할 수 있도록 합니다. (기능 완성 및 레이아웃 최적화 완료)
*   **API 서버**: `src/api/` (FastAPI) 연동 및 히스토리 데이터 제공.
*   **UI 개발**: `trade-front/` (React+Vite + TailwindCSS)
    *   **Dashboard**: 시장 온도계 및 주도주 퍼포먼스 차트.
    *   **Survival Chart**: 손절선(Shield) 시각화 및 포지션 사이징 계산기 통합.
    *   **Layout Fix [v9.5]**: 모바일 및 다양한 해상도에서의 차트 잘림 방지 및 뷰포트 최적화 적용.
    *   **Explorer**: 실시간 퀀트 엔진 탐색기 구현.

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