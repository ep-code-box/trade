# 🎯 TrendHunter 보안 및 운영 마스터 블루프린트 (v3.1)

## 1. 하이브리드 리소스 공유 모델
| 기능 영역 | 데이터 소스 (API Key) | 권한 범위 | 상세 설명 |
| :--- | :--- | :--- | :--- |
| **Market Intelligence** | **Owner's KIS Key** | 전 사용자 (Read) | 시세/RS 연산 (AI 불필요, 통계 기반) |
| **Stock Screener** | **Owner's KIS Key** | 전 사용자 (Read) | 마스터의 원칙(VCP 등) 적용 공유 |
| **AI Mentoring** | **User's Gemini Key**| **선택적 (R/W)** | **키 등록 사용자만 활성화** (On-demand) |
| **Account / Assets** | **User's KIS Key** | 본인 한정 (R/W) | 본인 잔고 및 개인 매매 내역 |
| **Trading Order** | **User's KIS Key** | 본인 한정 (R/W) | **User Bot** 승인 필수, 현금 전용 |
| **System Admin** | **Master Bot** | **Owner Only** | 서버 로그 및 전체 업데이트 제어 |

---

## 2. 런타임 및 인프라 보안 (Infrastructure Hardening)
| 리스크 항목 | 방어 기제 | 상세 내용 |
| :--- | :--- | :--- |
| **데이터 오염** | **Cross-Check** | 지수 괴리율 검증 로직으로 조작된 리포트 발행 차단 |
| **봇 권한 탈취** | **Webhook Shield** | 텔레그램 공식 IP 화이트리스트 및 Secret Token 헤더 검증 |
| **DB 잠금/DoS** | **WAL & Quota** | SQLite WAL 모드 적용 및 사용자별 자원 할당량(Quota) 제한 |
| **메모리 스크래핑** | **RAM Cleansing** | API 호출 직후 평문 변수 즉시 삭제 및 메모리 정리(GC) |

---

## 3. 금융 안전장치 (Financial Guardrails)
| 리스크 항목 | 방어 기제 | 시스템의 행동 |
| :--- | :--- | :--- |
| **신용/미수 공격** | **Cash-Only Force** | 코드 레벨에서 신용 파라미터 차단, 오직 현금 주문만 허용 |
| **자산 전량 매도** | **Contextual 2FA** | 주문 상세 정보(종목/금액)를 포함한 텔레그램 최종 승인 |
| **광기 매매 (Panic)** | **Trading Limits** | 1회 최대 금액(500만), 일일 한도(2천만) 초과 시 주문 거부 |
| **비상 상황** | **Emergency Kill** | 텔레그램 버튼 하나로 모든 주문 취소 및 서버 즉시 셧다운 |

---

## 4. 사용자별 설정 격리 및 암호화
*   **저장 보안**: 모든 API 키는 **AES-256-CBC**로 암호화하여 DB에 저장 (Key는 서버 환경변수).
*   **세션 보안**: 세션 발급 시 `IP` + `User-Agent` 지문을 바인딩하고, 1시간마다 로테이션 수행.
*   **접근 제어**: 모든 API는 `Depends(get_current_user)`를 통해 요청자의 소유권과 권한을 검증.