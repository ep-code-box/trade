# Trade (TrendHunter) 실행 메뉴얼

> **기능 정리:** `FUNCTIONALITY_MAP.md` | **운영 흐름·GCP 배포:** `ROADMAP.md`

---

## 1. 환경 설정

- **Python:** 3.x, 가상환경 권장 (`python -m venv .venv`)
- **의존성:** `pip install -r requirements.txt`
- **환경 변수:** `.env`에 `APP_KEY`, `APP_SECRET`, `MODE`(real/vts) 설정
- **토큰:** KIS API 토큰은 `auth_helper`가 `kis_token.json`에 저장·재사용  
  (리팩토링 후: `src.auth` 사용 시 동일 경로)

---

## 2. DB 스키마 요약

- 상세: `DB_DESIGN.md`, 실제 사용 컬럼: `FUNCTIONALITY_MAP.md` §8
- **stock_info.db:** `master_info`, `daily_analysis`, `sectors_themes`
- **초기화:** `python db_manager.py` 또는 `python run_init.py` (리팩토링 경로: `src.db` 사용)
- **뷰:** `python setup_views.py` → `view_trend_candidates`, `view_dividend_candidates`

---

## 3. 스크립트 역할 요약

| 구분 | 스크립트 | 역할 (한 줄) |
|------|----------|--------------|
| 인프라 | auth_helper.py | KIS 토큰 발급·저장 |
| 인프라 | db_manager.py | DB 테이블 생성 |
| 인프라 | setup_views.py | Track1/Track2 뷰 생성 |
| 동기화 | db_sync.py | KOSPI/KOSDAQ 마스터 → master_info |
| 동기화 | db_sync_themes.py | DWS 업종/테마 ZIP → sectors_themes |
| 수집 | fetch_daily_price.py | 일봉·지표 → daily_analysis |
| 수집 | fetch_stock_fundamentals.py | PER/PBR 등 → master_info |
| 수집 | fetch_dividend_* | 배당 DPS/수익률 → master_info, daily_analysis |
| 수집 | mine_dividend_* | 전수/업종별 배당 → master_info, daily_analysis |
| 태깅 | tag_dividend_cycles*.py | 배당 빈도 → dividend_cycle, dividend_count |
| 분석 | calc_rs_score.py | RS 점수 → daily_analysis(최신일) |
| 분석 | recalc_indicators.py | SMA·vol_std 등 전량 재계산 |
| 분석 | screen_market.py | Track1/Track2 리포트 출력 |
| 스크립트 | compare_*, check_*, debug_*, test_* | 비교·검증·디버그 |

상세(입력/출력/의존성): `FUNCTIONALITY_MAP.md`

---

## 4. 실행 흐름 (권장 순서)

### 4.1 최초 1회
1. `.env` 설정, `pip install -r requirements.txt`
2. `python db_manager.py` — 테이블 생성
3. `python setup_views.py` — 뷰 생성 (데이터 없으면 뷰는 빈 결과)
4. **마스터:** `kospi_code.mst`, `kosdaq_code.mst` 준비 후 `python db_sync.py`
5. **테마:** `python db_sync_themes.py` (DWS에서 idxcode.mst, theme_code.mst 다운로드)
6. **일봉:** `python fetch_daily_price.py` — 전 종목 일봉·지표 수집
7. **RS:** `python calc_rs_score.py` — 최신일 RS 점수
8. **배당:** 아래 4.2 중 하나 이상 실행
9. `python setup_views.py` 재실행 (데이터 반영 후 뷰 갱신)
10. `python screen_market.py` — 리포트 확인

### 4.2 배당 데이터 채우기 (택일 또는 조합)
- **순위 API 일괄:** `python fetch_dividend_all.py` 또는 `python fetch_high_dividend_rank.py`
- **종목별 기본정보(실전):** `python fetch_dividend_info_final.py` 또는 `python mine_dividend_full_sweep.py`
- **배당 주기 태깅:** `python tag_dividend_cycles.py` 또는 `tag_dividend_cycles_full.py` 또는 `tag_dividend_cycles_ultimate.py`

### 4.3 일일 배치 (예시)
1. `python fetch_daily_price.py` — 일봉 갱신
2. `python calc_rs_score.py` — RS 갱신
3. (선택) 배당 수집/태깅
4. `python screen_market.py` — 리포트

### 4.4 수동 분석·검증
- 스크리닝: `python screen_market.py`
- 배당 비교: `python compare_dividend_sources.py`
- 샘플 검증: `python check_sample_calculation.py`
- API 디버그: `python debug_api.py`, `python fetch_dividend_debug.py`

---

## 5. 트러블슈팅

- **토큰 만료:** `kis_token.json` 삭제 후 재실행 시 재발급
- **실전/모의 URL:** 배당 관련 API 대부분은 **실전 도메인**만 지원 → `MODE=real` 및 실전 URL 사용 스크립트 확인
- **DB 경로:** 기본 `TrendHunter/db/stock_info.db` (루트 기준)
- **뷰 컬럼 없음:** `view_trend_candidates`는 `volume_sma_50`, `vol_std_10d` 등 필요 → `fetch_daily_price.py` 또는 `recalc_indicators.py` 실행 후 뷰 재생성

---

---

## 6. 리팩토링 후 실행 (공통 모듈 사용)

**통합 CLI:** `python run.py` (명령 없이 실행 시 목록), `python run.py <명령>`  
예: `python run.py init`, `python run.py daily`, `python run.py screen`

| 명령 | 설명 |
|------|------|
| init | DB 테이블 생성 |
| views | Track1/Track2 뷰 생성 |
| sync | 마스터 동기화 (kospi_code.mst, kosdaq_code.mst) |
| themes | 테마/업종 동기화 (DWS 다운로드) |
| daily | 일봉 수집 |
| fundamentals | 펀더멘털 수집 |
| dividend | 배당 DPS(실전) |
| dividend-all | 배당 순위 일괄 |
| dividend-rank | 고배당 순위 |
| mine | 업종별 배당 마이닝 |
| mine-sweep | 전 종목 배당 전수 |
| tag | 배당 주기 태깅 |
| tag-full | 예탁원 배당일정 태깅 |
| tag-ultimate | 업종별 배당 태깅 |
| rs | RS 점수 계산 |
| recalc | 지표 전량 재계산 |
| screen | Track1/Track2 리포트 |
| compare | 배당 소스 비교 |
| check | 샘플 검증 |
| debug | API 디버그 |
| test-div | 배당 샘플 테스트 |

**모듈 직접 실행:** `python -m src.jobs.fetch_daily_price`, `python -m src.analysis.screen_market` 등 (위 표와 동일 기능).

- **공통 모듈:** `src/config.py`, `src/auth.py`, `src/kis_api.py`, `src/db/`
- **기존 루트 스크립트:** 삭제 완료. 실행은 `run.py`·`src` 모듈만 사용.

*기능 상세: `FUNCTIONALITY_MAP.md` | 리팩토링 계획: `REFACTOR_PLAN.md`*
