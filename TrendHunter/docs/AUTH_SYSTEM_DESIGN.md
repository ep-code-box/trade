# TrendHunter Hybrid Auth & Data Architecture (v2.2)

## 1. 아키텍처 전략: 하이브리드 공유 모델
본 시스템은 분석 데이터의 일관성과 실행의 보안을 동시에 달성하기 위해 **공유 지능(Shared Intelligence)**과 **개별 실행(Private Execution)** 레이어를 분리한다.

### 1.1 레이어 정의
*   **Intelligence Layer (공유)**: 마스터(Owner)의 리소스로 생성된 시장 분석 결과물. 모든 사용자가 동일한 Source of Truth를 공유한다.
*   **Execution Layer (격리)**: 개별 사용자의 자산이 움직이는 영역. 철저히 개별 사용자의 API 키로만 작동한다.

---

## 2. 리소스별 API 키 및 권한 매핑

| 기능 카테고리 | 리소스 (Data/API) | 사용 API 키 | 접근 권한 |
| :--- | :--- | :--- | :--- |
| **Market Intelligence** | Daily Analysis, RS Score, Explorer, Reports | **Owner's Key** | 전 사용자 (Read) |
| **Trading Execution** | Account Balance, Buy/Sell Orders, Trading Bot | **User's Key** | 본인 한정 (R/W) |
| **AI Mentoring** | Chatbot Analysis, Portfolio Review | **User's Key** | 본인 한정 (R/W) |
| **System Admin** | Log Stream, Batch Job Trigger, User Mgmt | **System Default** | **Owner Only** |

---

## 3. 데이터베이스 스키마 명세

### 3.1 `users` (사용자 식별)
```sql
CREATE TABLE users (
    username TEXT PRIMARY KEY,
    telegram_id TEXT UNIQUE,        -- 텔레그램 고유 숫자 ID
    role TEXT CHECK(role IN ('OWNER', 'GUEST')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2 `system_config` (사용자 설정 격리 및 암호화)
```sql
CREATE TABLE system_config (
    username TEXT,
    key TEXT,                       -- KIS_APP_KEY, KIS_SECRET, GEMINI_API_KEY 등
    value TEXT,                     -- AES-256-CBC 암호화된 값
    updated_at TEXT,
    PRIMARY KEY (username, key),
    FOREIGN KEY (username) REFERENCES users(username)
);
```

---

## 4. 인증 및 권한 로직 (Middleware)

### 4.1 세션 검증 프로세스 (Fingerprinting)
1.  **Identity**: `/api/auth/chat` (텔레그램 연동)을 통해 신원 식별.
2.  **Fingerprinting**: 세션 생성 시 클라이언트의 `IP` + `User-Agent`를 해싱하여 세션에 바인딩.
3.  **Validation**: 모든 요청 시 브라우저 지문을 대조하며, 불일치 시 즉시 세션을 파기하고 재인증 요구.

---

## 5. 예외 처리 및 운영 안정성 (Reliability)

1.  **TPS 제어**: 서버 공통 Rate Limiter를 도입하여 IP당 KIS 호출 빈도를 초당 3회 이하로 제어한다.
2.  **데이터 동기화 감시**: 공유 데이터의 최신 업데이트 시간을 추적하여 30분 이상 지연 시 전 사용자에게 경고를 표시한다.
3.  **Emergency Access**: 텔레그램 장애 시를 대비해 환경변수 기반의 물리적 마스터 키(Hardcoded Secret) 경로를 유지한다.
4.  **DB 동시성**: SQLite **WAL(Write-Ahead Logging) 모드**를 활성화하고 Write 작업에 Retry 로직을 적용한다.

---

## 6. 최상위 보안 설계 (Paranoid Security)

### 6.1 API 키 암호화 (At-Rest Encryption)
*   DB에 저장되는 모든 민감 정보(`value`)는 서버의 환경변수(`ENCRYPTION_KEY`)를 기반으로 **AES-256** 암호화하여 저장한다. DB 파일이 유출되어도 서버 외부에서는 복호화가 불가능하도록 한다.

### 6.2 실행 단계 2차 인증 (Execution 2FA)
*   **주문 실행 시 승인**: 매수/매도 등 자산 변동 행위 발생 시, 즉시 집행하지 않고 텔레그램으로 승인 버튼을 전송한다. 사용자가 텔레그램에서 승인 버튼을 누른 경우에만 거래소로 주문을 전송한다.

### 6.3 세션 하이재킹 원천 차단
*   모든 세션 쿠키는 `HttpOnly`, `Secure`, `SameSite=Lax` 속성을 필수로 적용하며, 클라이언트 사이드 스크립트의 접근을 불허한다.

### 6.4 IP Locking (KIS Policy)
*   사용자 설정 시 KIS API 페이지에서 서버의 고정 IP만 접속 가능하도록 화이트리스트 등록을 강력하게 권고하고 가이드를 제공한다.
