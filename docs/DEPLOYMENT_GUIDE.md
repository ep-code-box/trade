# TrendHunter 배포 가이드 (Deployment Guide)

## 1. 로컬 통합 배포 (Local Production)
현재 시스템은 단일 서버 통합 구조로 배포됩니다.
*   **스크립트**: `./run_production.sh`
*   **프로세스**: 
    1.  `trade-front`에서 React 빌드 (`dist` 생성).
    2.  FastAPI 서버(`src/api/main.py`)가 `dist` 서빙 시작.
    3.  모든 로그는 `logs/` 폴더에 기록됨.

## 2. GCP 무료 스택 배포 전략 (Cloud Zero-Cost)
GCP Free Tier를 활용하여 비용 없이 24시간 운영하는 전략입니다.

### 핵심 구성
*   **Runtime**: Google Cloud Run (Serverless)
*   **Storage**: Google Cloud Storage (GCS) - SQLite 파일 영구 보관용
*   **CI/CD**: Cloud Build

### 데이터 보존 로직 (GCS Sync)
Cloud Run 인스턴스는 종료 시 내부 파일이 삭제되므로, 다음 로직을 반드시 준수합니다.
1.  **시작 시**: GCS 버킷에서 최신 `stock_info.db` 다운로드.
2.  **동작 시**: 로컬 SQLite 수정.
3.  **중요 쓰기 발생 시**: 즉시 GCS로 비동기 업로드 (Write-Through).
4.  **종료 시**: 최종 DB 상태를 GCS에 백업.

---

## 3. 환경 변수 설정 (Security Keys)
배포 환경에서는 다음 환경 변수가 필수적으로 설정되어야 합니다.

| 변수명 | 설명 |
| :--- | :--- |
| `ENCRYPTION_KEY` | DB 암호화용 AES 키 |
| `MASTER_BOT_TOKEN` | OWNER 전용 봇 토큰 |
| `CLIENT_BOT_TOKEN` | 일반 사용자용 봇 토큰 |
| `WEBHOOK_SECRET` | 텔레그램 웹훅 보안 토큰 |
| `GEMINI_API_KEY` | (시스템 기본용 - 선택 사항) |
