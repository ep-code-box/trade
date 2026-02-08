# 📋 TrendHunter Development TODO List

## Phase 1: Security & Identity Core (보안 및 신원 기반 구축)
- [ ] **보안 모듈 개발**: AES-256 기반 API 키 암호화/복호화 모듈 구현 (`src/utils/security.py`).
- [ ] **DB 스키마 확장**: 설계서 v2.2에 따른 `users`, `system_config`, `auth_sessions` 테이블 생성.
- [ ] **사용자별 설정 격리**: `src/auth.py` 리팩토링하여 세션별 동적 API 키 로딩 구현.
- [ ] **텔레그램 봇 연동**: 
    - [ ] Master Bot (관제용) 연동 및 Webhook 서버 구축.
    - [ ] User Bot (인증/2FA용) 연동 로직 구현.
- [ ] **3단계 관문 UI**: 챗봇 형태의 Gatekeeper 로그인 화면 구현 (`Login.tsx`).

## Phase 2: Hybrid Data & Order Flow (데이터 공유 및 주문 강화)
- [ ] **공유 지능 레이어**: 마스터(`admin`)의 키로 `daily_analysis`를 업데이트하는 통합 배치 작업 정교화.
- [ ] **실행 레이어 격리**: 계좌 조회 및 주문 시 개별 사용자의 암호화된 키 복호화 및 적용.
- [ ] **2FA 주문 승인**: 매수/매도 시 텔레그램 승인 메시지 발송 및 웹훅 응답 처리 로직.
- [ ] **금융 안전장치**: 신용 주문 차단 및 일일 거래 한도(Hard Limit) 로직 반영.

## Phase 3: Monitoring & Administration (관제 시스템)
- [ ] **System Audit 패널**: OWNER 전용 로그 스트리밍(`tail -f`) 및 프로세스 제어 UI.
- [ ] **데이터 헬스 모니터링**: 데이터 업데이트 지연 시 자동 알림 및 경고 표시.

## Phase 4: Cloud Deployment (GCP Zero-Cost Stack)
- [ ] **Containerization**: `Dockerfile` 및 `docker-compose.yml` 작성.
- [ ] **GCS SQLite Sync**: Cloud Run의 휘발성 방지를 위한 SQLite-GCS 동기화 모듈 개발.
- [ ] **GCP Infrastructure**: Cloud Run, Cloud Storage, Cloud Scheduler 설정 및 배포 스크립트.

## Phase 5: Optimization & Cleanup (최적화 및 정리)
- [ ] **Refactoring**: `GEMINI.md`의 라인 수 제한(200-300줄) 원칙에 따른 모듈 분리.
- [ ] **Test Suite**: 파편화된 테스트 스크립트를 `src/tests/`로 정식 통합.
- [ ] **External Cleanup**: `open-trading-api-main` 등 외부 폴더 정리 및 필요한 로직 내재화.
