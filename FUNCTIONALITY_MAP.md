# 기능 정리 (명령어·모듈별 상세 역할 및 데이터 흐름)

> **리팩토링 후** `src/` 구조 및 `run.py` 진입점 기준 통합 가이드.
> 각 모듈의 구체적인 역할과 입출력 데이터, 의존성을 상세히 기술함.

---

## 1. 시스템 기초 및 설정 (Infrastructure)

| 명령어 (run.py) | 모듈 (src/) | 상세 역할 (Description) | 입력 (Input) | 출력 (Output) |
|:--- |:--- |:--- |:--- |:--- |
| **init** | `db.manager` | **DB 초기화**: `stock_info.db` 파일이 없으면 생성하고, `master_info`, `daily_analysis`, `trade_plan` 등 핵심 테이블 스키마를 정의함. | 없음 | `stock_info.db` (Schema) |
| **views** | `scripts.setup_views` | **분석 뷰 생성**: 복잡한 SQL 쿼리(Track 1 조건 등)를 미리 정의한 View(`view_trend_candidates`)를 생성하여 분석 효율을 높임. | `daily_analysis` | View 생성 |
| **sync** | `jobs.db_sync` | **마스터 동기화**: KIS에서 제공하는 `kospi_code.mst`, `kosdaq_code.mst` 파일을 파싱하여 종목 기본 정보(이름, 시장구분 등)를 DB에 적재. | `.mst` 파일 | `master_info` (Insert/Update) |
| **themes** | `jobs.db_sync_themes` | **테마 동기화**: DWS 서버에서 테마/업종 코드 ZIP을 다운로드 및 파싱하여 종목과 테마의 관계를 매핑. | DWS URL (ZIP) | `sectors_themes` |

---

## 2. 데이터 수집 (Data Collection Pipeline)

| 명령어 | 모듈 (src/jobs/) | 상세 역할 및 핵심 로직 | 입력 | 출력 |
|:--- |:--- |:--- |:--- |:--- |
| **daily** | `fetch_daily_price` | **일봉/지표 수집**: 전 종목의 일봉(OHLCV)을 수집하고, SMA(20/50/200), 거래량 이평, 변동성(Vol Std) 등 기술적 지표를 즉시 계산하여 저장. (최대 200일 버퍼 활용) | KIS API (Daily) | `daily_analysis` (Rows & Indicators) |
| **fundamentals** | `fetch_stock_fundamentals` | **재무제표 수집**: PER, PBR, 영업이익, 당기순이익 등 펀더멘털 지표를 수집하여 우량주 필터링(흑자 여부)에 사용. | KIS API (Info) | `master_info` (Update columns) |
| **supply** | `fetch_supply_history` | **수급 수집**: 외국인, 기관, 연기금 등 투자 주체별 일별 순매수량을 수집하여 "메이저 수급" 여부를 판단. | KIS API (Investor) | `daily_analysis` (Net Buy cols) |
| **dividend-all** | `fetch_dividend_all` | **배당 순위 수집**: 배당수익률 상위 종목 리스트를 빠르게 긁어와서 배당 정보를 일괄 업데이트. (약식) | KIS API (Ranking) | `master_info` (Dividend Info) |
| **mine** | `mine_dividend_data` | **배당 마이닝**: 업종별로 정밀 스캔하여 종목별 DPS(주당배당금)와 배당 주기(월/분기/연)를 분석 및 태깅. (정밀) | KIS API (Sector) | `master_info` (Cycle, Count) |

---

## 3. 분석 및 전략 실행 (Analysis & Strategy)

| 명령어 | 모듈 (src/analysis/) | 상세 역할 및 알고리즘 | 입력 | 출력 |
|:--- |:--- |:--- |:--- |:--- |
| **rs** | `calc_rs_score` | **RS 점수 계산**: 전체 3,800+ 종목의 최근 3/6/9/12개월 수익률에 가중치를 두어 종합 점수를 매기고, 이를 백분위(1~99)로 환산하여 저장. (Market Leader 식별의 핵심) | `daily_analysis` (Close) | `daily_analysis` (`rs_score`) |
| **recalc** | `recalc_indicators` | **지표 재계산**: 로직 변경 시 과거 모든 데이터에 대해 이평선, 볼린저밴드, VCP 지표 등을 다시 계산하여 정합성 확보. | `daily_analysis` (Raw) | `daily_analysis` (Indicators) |
| **screen** | `screen_market` | **통합 리포트**: 수집된 모든 데이터(기술적+기본적)를 종합하여 Track 1(추세), Track EX(모멘텀), Track 2(배당) 유망 종목을 선별하고 `trade_plan`에 저장. | All Tables | Console Report, `trade_plan` |

---

## 4. 핵심 데이터 흐름 (Data Flow Architecture)

1.  **Init & Sync**: `stock_info.db`의 골격을 만들고 종목 리스트를 채웁니다.
2.  **Daily Collection**: 매일 장 종료 후 `daily` 명령어로 시세와 지표를 업데이트합니다.
3.  **Context Enrichment**: `fundamentals`, `supply`, `mine`을 통해 재무/수급/배당 정보를 보강합니다.
4.  **Analysis**: `rs`로 전체 순위를 매기고, `screen`으로 최종 매매 후보를 도출합니다.
5.  **Execution**: (Future) `trade_plan`에 저장된 종목을 실제 API로 주문합니다.

---

## 5. 주요 파일 및 경로

*   **src/auth.py**: 토큰 발급/갱신 및 URL(모의/실전) 라우팅 담당.
*   **src/kis_api.py**: `requests` 라이브러리를 래핑하여 API 호출, 헤더 처리, Rate Limit(초당 제한) 준수.
*   **src/db/manager.py**: SQLite 연결 객체 제공 및 스키마 버전 관리.
*   **MANUAL.md**: 시스템 운영 및 문제 해결을 위한 상세 가이드.
