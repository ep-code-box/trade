# 기능 정리 (스크립트별 역할·입출력·의존성)

> 리팩토링 전 **기존 소스 기준**으로 정확히 정리한 문서.

---

## 1. 인프라·설정

| 파일 | 역할 (한 줄) | 입력 | 출력 | 의존성 |
|------|----------------|------|------|--------|
| **auth_helper.py** | KIS API 토큰 발급·저장 | .env(APP_KEY, APP_SECRET, MODE) | kis_token.json, access_token | requests, dotenv |
| **db_manager.py** | DB 스키마 생성(master_info, daily_analysis, sectors_themes) | 없음 | stock_info.db 테이블 | sqlite3 |
| **setup_views.py** | Track1/Track2 후보 뷰 생성 | stock_info.db | view_trend_candidates, view_dividend_candidates | sqlite3 |

---

## 2. 데이터 동기화 (마스터·테마)

| 파일 | 역할 (한 줄) | 입력 | 출력 | 의존성 |
|------|----------------|------|------|--------|
| **db_sync.py** | KOSPI/KOSDAQ 마스터 파싱 후 DB 적재 | kospi_code.mst, kosdaq_code.mst, db_manager | master_info | db_manager.init_dbs, pandas |
| **db_sync_themes.py** | DWS에서 업종/테마 ZIP 다운로드 후 sectors_themes 적재 | DWS URL(idxcode.mst.zip, theme_code.mst.zip), db_manager | sectors_themes | db_manager.init_dbs |

---

## 3. 데이터 수집 (API → DB)

| 파일 | 역할 (한 줄) | 입력 | 출력 | 의존성 |
|------|----------------|------|------|--------|
| **fetch_daily_price.py** | 종목별 일봉·지표(SMA, vol_std, high_52w 등) 수집·저장 | master_info, auth | daily_analysis | BASE_URL, FHKST03010100 |
| **fetch_stock_fundamentals.py** | 주식현재가 상세(PER/PBR 등) 조회 후 master_info 업데이트 | master_info, auth | master_info(per, pbr 등) | BASE_URL, FHKST01010100 |
| **fetch_dividend_info.py** | 주식기본조회(배당) — **BASE_URL 사용** (모의 가능) | master_info, auth | master_info(per_stock_dvdn_amt), daily_analysis(dividend_yield) | CTPF40020000 |
| **fetch_dividend_info_final.py** | 주식기본조회(배당) — **실전 전용** | master_info(ST), auth | 동일 | REAL_BASE_URL, CTPF40020000 |
| **fetch_dividend_all.py** | 배당순위 API로 코드 보정·연간 DPS 합산 후 DB 반영 | auth | master_info(per_stock_dvdn_amt), daily_analysis(dividend_yield) | REAL_BASE_URL, HHKDB13470100 |
| **fetch_high_dividend_rank.py** | 배당순위 API(코스피/코스닥·결산/중간) → master_info + daily_analysis | auth | 동일 | REAL_BASE_URL, HHKDB13470100 |
| **fetch_dividend_yield_complete.py** | 재무비율 API(est_yield)로 배당수익률만 daily_analysis 업데이트 | master_info(ST), auth | daily_analysis(dividend_yield) | BASE_URL, FHKST01010400 |
| **mine_dividend_data.py** | 업종별 배당순위 API 여러 번 호출 → DPS·주기·count 합산 후 DB | auth | master_info(per_stock_dvdn_amt, dividend_cycle, dividend_count), daily_analysis | REAL_BASE_URL, HHKDB13470100 |
| **mine_dividend_full_sweep.py** | 전 종목 주식기본조회(CTPF1002R)로 DPS·PER/PBR 수집 | master_info(6자리 코드), auth | master_info, daily_analysis(dividend_yield) | REAL_BASE_URL, CTPF1002R |

---

## 4. 배당 주기 태깅 (API 또는 이벤트 → DB)

| 파일 | 역할 (한 줄) | 입력 | 출력 | 의존성 |
|------|----------------|------|------|--------|
| **tag_dividend_cycles.py** | 배당순위 API(코스피/코스닥·결산/중간) → 빈도 카운트 → dividend_cycle, dividend_count | auth | master_info(dividend_cycle, dividend_count) | REAL_BASE_URL, HHKDB13470100 |
| **tag_dividend_cycles_full.py** | 예탁원 배당일정 API(기간별) → 전수 이벤트 카운트 → dividend_cycle, dividend_count | auth | master_info(dividend_cycle, dividend_count) | REAL_BASE_URL, HHKDB669102C0 |
| **tag_dividend_cycles_ultimate.py** | sectors_themes(SECTOR_MASTER) 기준 업종별 배당순위 수집 → 카운트·주기 DB 업데이트 | sectors_themes, auth | master_info(dividend_cycle, dividend_count) | REAL_BASE_URL, HHKDB13470100 |

---

## 5. 지표 재계산·분석 (DB만 사용)

| 파일 | 역할 (한 줄) | 입력 | 출력 | 의존성 |
|------|----------------|------|------|--------|
| **calc_rs_score.py** | daily_analysis 종가 기준 RS 점수 계산 → **최신일만** rs_score 업데이트 | daily_analysis | daily_analysis(rs_score) | sqlite3, pandas |
| **recalc_indicators.py** | daily_analysis 전량 읽어 SMA·vol_std·high_52w·volume_sma_50 재계산 후 **전체 덮어쓰기** | daily_analysis | daily_analysis(전체) | sqlite3, pandas |
| **screen_market.py** | view_trend_candidates + view_dividend_candidates + sectors_themes 조합해 Track1/Track2 리포트 출력 | daily_analysis, master_info, sectors_themes, 뷰 | 콘솔 리포트 | sqlite3, pandas |

---

## 6. 스크립트(비교·검증·디버그)

| 파일 | 역할 (한 줄) | 입력 | 출력 | 의존성 |
|------|----------------|------|------|--------|
| **compare_dividend_sources.py** | KIS API vs pykrx 배당 수익률 비교 (특정 종목) | auth, pykrx | 콘솔 | REAL_BASE_URL, HHKDB13470100 |
| **check_sample_calculation.py** | 특정 종목 SMA20·배당수익률 직접 계산 vs DB 값 검증 | stock_info.db | 콘솔 | sqlite3, pandas |
| **debug_api.py** | 배당순위 API 원천 데이터 샘플 1건 출력 | auth | 콘솔 | REAL_BASE_URL, HHKDB13470100 |
| **fetch_dividend_debug.py** | 배당순위 API 수집 후 master_info/daily_analysis 존재 여부 확인하며 동기화 디버그 | auth, DB | 콘솔·DB | REAL_BASE_URL |
| **test_dividend_sample.py** | 특정 종목(SK텔레콤) 배당 기록 조회·DPS 합산·DB dividend_yield 업데이트 | auth, DB | 콘솔·DB | REAL_BASE_URL |

---

## 7. 실행 흐름 (권장 순서)

### 7.1 최초 1회
1. `.env` 설정 (APP_KEY, APP_SECRET, MODE)
2. `python db_manager.py` — 테이블 생성
3. `python setup_views.py` — 뷰 생성 (이때 daily_analysis 등 데이터 없으면 뷰는 빈 결과)
4. **마스터:** `kospi_code.mst`, `kosdaq_code.mst` 준비 후 `python db_sync.py`
5. **테마:** `python db_sync_themes.py` (DWS에서 idxcode.mst, theme_code.mst 다운로드 후 sectors_themes 적재)
6. **일봉:** `python fetch_daily_price.py` — 전 종목 일봉·지표 수집
7. **RS:** `python calc_rs_score.py` — 최신일 RS 점수
8. **배당:** 아래 7.2 중 하나 이상 실행
9. `python setup_views.py` 재실행(데이터 반영 후 뷰 갱신)
10. `python screen_market.py` — 리포트 확인

### 7.2 배당 데이터 채우기 (택일 또는 조합)
- **순위 API 일괄:** `fetch_dividend_all.py` 또는 `fetch_high_dividend_rank.py`
- **종목별 기본정보(실전):** `fetch_dividend_info_final.py` 또는 `mine_dividend_full_sweep.py`
- **배당 주기 태깅:** `tag_dividend_cycles.py` 또는 `tag_dividend_cycles_full.py` 또는 `tag_dividend_cycles_ultimate.py`

### 7.3 일일 배치 (예시)
1. `python fetch_daily_price.py` — 일봉 갱신
2. `python calc_rs_score.py` — RS 갱신
3. (선택) 배당 수집/태깅
4. `python screen_market.py` — 리포트

---

## 8. DB 스키마 요약 (실제 사용 컬럼)

- **master_info:** code(PK), name, market_type, scrt_grp_cls_code, per_stock_dvdn_amt, dividend_cycle, dividend_count, per, pbr, stck_sdpr, sale_account, bsop_prfi, thtr_ntin, updated_at 등
- **daily_analysis:** (date, code) PK, close, volume, amount, market_cap, sma_20, sma_50, sma_150, sma_200, high_52w, low_52w, rs_score, vol_std_10d, vol_std_50d, dividend_yield, volume_sma_50
- **sectors_themes:** code, category_type(SECTOR_MASTER / THEME), category_name, source
- **뷰:** view_trend_candidates(일봉 최신일 + 조건), view_dividend_candidates(배당·흑자 등)

---

*리팩토링 시 이 문서를 기준으로 새 진입점·폴더 매핑.*
