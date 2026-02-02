# TrendHunter 기능 명세 및 기술 백서 (Master's Edition)

시스템의 모든 로직은 시장의 거장들(Livermore, O'Neil, Minervini)의 원칙을 정량화하여 따릅니다.

---

## 1. 핵심 분석 엔진: 생존형 필터 (The Survival Filter)

### 1.1 트랙 1: 추세 추종 (Leader's Law)
단순한 상승주가 아닌, 시장을 압도하는 **'진짜 리더'**만 선별합니다.
*   **RS Score**: **90점 이상** 필수 (상위 10%의 강도).
*   **VCP Tightness**: 변동성 수축이 **10% 이내**일 때만 매수 사정권(Pivot)으로 간주.
*   **Safety Net**: 현재가가 설정된 손절선(Stop-Loss)을 하회하거나 박스 하단을 이탈할 경우 즉시 'CANCEL'.
*   **Check Item**: 체결 강도가 80% 미만일 경우 매수세 실종으로 판단, 실행을 보류함.

### 1.2 트랙 2: 배당주 (The Orthodox Dividend v6.0)
단순한 랭킹 API가 아닌, **재무제표의 배당 이력**을 추적하여 배당의 질을 검증합니다.
*   **역산 로직**: `(결산 당기순이익 / 상장주수) * 배당성향(Payout Ratio)` 공식을 통해 진짜 배당금을 도출.
*   **결산 데이터 우선**: 분기/반기 노이즈를 제거하기 위해 **12월 결산 보고서** 데이터를 최우선적으로 추적.
*   **지속성 검증**: ROE 10% 이상, 흑자 지속성, 영업이익률 캡핑(100% 한도) 등을 통해 데이터 오류와 부실 기업을 차단.

---

## 2. 데이터 흐름 및 명령어 (The Standard Routine)

| 단계 | 명령어 | 정석 로직 (The Truth) |
|:--- |:--- |:--- |
| **Ingestion** | `daily` | KIS OHLCV 수집 및 SMA 50/150/200 계산 |
| **Enrichment** | `fundamentals` | **[v6.0]** 결산 재무제표 기반 배당 역산 및 ROE 수집 |
| **Analysis** | `rs` | 전 종목 가중 수익률 기반 RS Rating (1~99) |
| **Selection** | `screen` | 스승의 잣대(RS 90+, VCP 10%) 기반 최종 선별 |
| **Summary** | `screen` | `market_summary` 테이블에 주도 섹터 및 시장 리스크 저장 |

---

## 3. 대시보드 시각화 철학 (The Dashboard)

*   **Master Dashboard**: `/api/summary`를 통해 시장의 '생존 가능성'을 먼저 진단.
*   **Technical View**: Track 1 종목은 3색 이평선과 PIVOT/STOP 라인을 통한 돌파 매매 시점 포착.
*   **Fundamental View**: Track 2 종목은 이평선보다 ROE, 영업이익률, 연간 예상 DPS 현금흐름에 집중.

---

## 4. 운영자의 행동 지침 (AI Mentor's Directive)
> "매일 매매하는 사람은 바보다. 현금도 비중이고, 인내는 가장 비싼 수업료다."
> 시스템은 데이터의 노예가 되어야 하며, 감정이 개입되는 순간 파멸임을 명심하십시오.
