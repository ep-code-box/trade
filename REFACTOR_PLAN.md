# 리팩토링 계획 (1차 완료 후 적용)

## 목표
1. **중복 코드 정리** — 공통 로직 모듈화
2. **정확한 흐름 파악 및 메뉴얼 작성** — 실행 순서·의존성 문서화
3. **폴더화** — 역할별 디렉터리 구조 정리

---

## 1. 중복 코드 정리

### 1.1 인증·API 공통화
| 현상 | 조치 |
|------|------|
| `get_access_token()`, `APP_KEY`, `APP_SECRET`를 스크립트마다 import | `auth_helper` 유지, **KIS API 호출 래퍼** 한 곳에서 제공 |
| `REAL_BASE_URL` vs `BASE_URL` 혼용 (일부는 `auth_helper.BASE_URL`, 일부는 로컬 `REAL_BASE_URL = "https://openapi.koreainvestment.com:9443"`) | `auth_helper`에 실전/모의 URL 통일 후, 스크립트는 `BASE_URL`만 사용 |
| API 호출 패턴 반복: `token → headers(appkey, appsecret, authorization) → requests.get(url, headers, params)` | **공통 함수** 예: `kis_get(path, params)`, `kis_post(path, body)` → 스크립트는 path/params만 전달 |

### 1.2 DB 접근 공통화
| 현상 | 조치 |
|------|------|
| `STOCK_DB_PATH = "TrendHunter/db/stock_info.db"` 다수 파일에 하드코딩 | `db_manager`(또는 `config`)에 경로 단일 정의, 나머지는 `from db_manager import STOCK_DB_PATH` 또는 `get_connection()` |
| `sqlite3.connect(STOCK_DB_PATH)` + cursor 반복 | `db_manager`에 `get_connection()`, `with_connection(callback)` 등 제공 후 스크립트는 해당 함수만 사용 |
| `master_info` / `daily_analysis` 등 업데이트 로직이 스크립트마다 조금씩 다름 | 스키마 기준으로 **읽기/쓰기 헬퍼** (예: `update_master_dividend(code, dps)`)를 `db_manager` 또는 전용 모듈로 통합 |

### 1.3 기타 반복
| 현상 | 조치 |
|------|------|
| `time.sleep(0.05)` 등 API 호출 간 쉬는 로직 분산 | 공통 API 래퍼 안에서 rate limit 처리 |
| `res.status_code == 200`, `data['rt_cd'] == '0'` 체크 반복 | 공통 래퍼에서 처리 후, 성공 시에만 파싱된 body 반환 |

---

## 2. 흐름 파악 및 메뉴얼 작성

### 2.1 실행 흐름 정리 (1차 완료 후 채울 항목)
- **초기 설정:** DB 생성·뷰 설정 (`db_manager.init_dbs`, `setup_views`) → 테마/마스터 동기화 (`db_sync`, `db_sync_themes`)
- **데이터 수집:** 일봉 → 배당 정보 → 펀더멘털 등 **실행 순서와 선행 조건** 명시
- **스크리닝/분석:** 어떤 스크립트가 어떤 DB/뷰에 의존하는지 의존성 그래프
- **실행 주기:** 수집·태깅·스크리닝을 매일/매주 어떤 순서로 돌릴지

### 2.2 메뉴얼 문서 구조 (MANUAL.md)
- **환경 설정:** `.env`, 가상환경, `requirements.txt`
- **DB 스키마 요약:** `DB_DESIGN.md` 요약 + 실제 사용 테이블/뷰
- **스크립트 역할 목록:** 파일명·한 줄 설명·입력(DB/API)·출력(DB/파일)
- **실행 가이드:** “처음 설치 후 1회”, “일일 배치”, “수동 분석” 시나리오별 명령/순서
- **트러블슈팅:** 자주 나오는 오류(토큰 만료, 실전/모의 URL, DB 경로 등)와 해결

---

## 3. 폴더화

### 3.1 제안 구조 (1차 코드 반영 후 조정)
```
trade/
├── .env
├── requirements.txt
├── README.md
├── MANUAL.md              # 실행 흐름·메뉴얼 (리팩토링 시 작성)
├── REFACTOR_PLAN.md       # 본 문서
├── GEMINI.md
├── DB_DESIGN.md
│
├── src/                   # 애플리케이션 코드
│   ├── __init__.py
│   ├── config.py          # STOCK_DB_PATH, BASE_URL 등 (또는 auth + db에서 import)
│   ├── auth.py            # auth_helper 이전·정리
│   ├── kis_api.py         # KIS API 공통 래퍼 (get/post, 헤더, rate limit)
│   ├── db/
│   │   ├── __init__.py
│   │   ├── manager.py     # db_manager: init_dbs, get_connection, 경로
│   │   └── queries.py     # 자주 쓰는 쿼리/업데이트 함수
│   ├── jobs/              # 데이터 수집·동기화
│   │   ├── sync_master.py
│   │   ├── sync_themes.py
│   │   ├── fetch_daily_price.py
│   │   ├── fetch_dividend_*.py
│   │   └── ...
│   ├── analysis/          # 스크리닝·태깅·분석
│   │   ├── tag_dividend_cycles*.py
│   │   ├── screen_market.py
│   │   └── ...
│   └── scripts/           # 1회성·디버그·비교
│       ├── compare_dividend_sources.py
│       ├── check_sample_calculation.py
│       └── ...
│
└── TrendHunter/
    ├── db/
    ├── charts/
    └── outputs/
```

**참고:** `open-trading-api-main/`은 **외부 참조용**이라 본인 코드가 아님. 리팩토링·폴더화 대상에서 제외. (.gitignore에 추가 권장)
```

### 3.2 분류 기준
- **jobs:** KIS/외부 API 호출·DB 적재까지 담당 (fetch, sync, mine)
- **analysis:** DB/뷰를 읽어 스크리닝·태깅·지표 계산 (tag, screen)
- **scripts:** 비교·샘플 검증·디버그 등 부가 스크립트

### 3.3 이동 시 유의
- `auth_helper` → `src/auth.py` (또는 `src/config.py`와 함께)
- `db_manager` → `src/db/manager.py`
- 루트의 `fetch_*`, `mine_*`, `tag_*` 등 → 위 역할에 맞게 `src/jobs`, `src/analysis`, `src/scripts`로 이동
- 실행 경로 변경에 따라 `STOCK_DB_PATH` 등은 **프로젝트 루트 기준**으로 한 곳에서 정의

---

## 4. 리팩토링 적용 순서 (권장)
1. **공통 모듈:** `auth` + KIS API 래퍼 + DB 연결/경로 통일 (중복 제거만으로도 효과 큼)
2. **폴더 구조:** `src/`, `jobs/`, `analysis/`, `scripts/` 생성 후 **새 진입점**만 추가 (기존 파일은 그대로 유지)
3. **흐름·메뉴얼:** 실행 순서와 의존성 정리 후 `MANUAL.md` 작성
4. **테스트:** 새 구조로 수집·태깅·스크리닝 한 번 돌려서 동작 검증
5. **정리:** 리팩토링 완료·검증 후에만 기존 루트 스크립트 삭제·통합

---

## 5. 기존 소스 처리 원칙
- **리팩토링 진행 중:** 기존 소스(`auth_helper.py`, `db_manager.py`, `fetch_*`, `mine_*`, `tag_*` 등)는 **일단 두고** 새 `src/`·새 진입점만 추가.
- **리팩토링 완료 후:** 새 구조로 동작 확인한 뒤에만 기존 파일 정리(삭제 또는 레거시 폴더로 이동).

---

*1차 개발이 끝나면 이 계획서를 기준으로 리팩토링 진행.*
