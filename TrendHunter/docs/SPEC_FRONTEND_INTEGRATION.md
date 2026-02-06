# [Milestone] 프론트엔드 통합 및 정적 자원 서빙 체계 구축

## 1. 개요 (Objective)
현재 이원화되어 운영 중인 백엔드(FastAPI)와 프론트엔드(React/Vite)의 실행 환경을 하나로 통합합니다. 이를 통해 인프라 복잡도를 낮추고, 단일 포트(8000)를 통한 서비스 제공으로 운영 효율성과 보안성(CORS 원천 차단)을 극대화하는 것을 목표로 합니다.

## 2. 핵심 아키텍처 변화 (Architectural Shift)

### 2.1 기존 구조 (Decoupled)
*   **Backend**: `localhost:8000` (API 전용)
*   **Frontend**: `localhost:5173` (Vite Dev Server 전용)
*   **문제점**: 배포 시 두 개의 프로세스 관리 필요, 브라우저의 CORS 정책 대응 필요.

### 2.2 통합 구조 (Unified)
*   **Build Artifact**: React 프로젝트를 프로덕션용 최적화 파일(`dist/`)로 빌드.
*   **FastAPI Static Mounting**: FastAPI 엔진이 루트 경로(`/`)에서 빌드된 정적 파일들을 직접 서빙.
*   **Single Endpoint**: 모든 서비스가 `localhost:8000` 하나로 통합되어 동작.

## 3. 세부 구현 전략 (Implementation Strategy)

### 3.1 프론트엔드 빌드 파이프라인
*   `trade-front/` 내에서 `npm run build`를 통해 자원 압축 및 난독화가 완료된 `dist/` 디렉토리 생성.
*   빌드 결과물은 백엔드가 즉시 참조 가능한 경로로 위치 지정.

### 3.2 백엔드 서빙 로직 (FastAPI)
*   `fastapi.staticfiles` 모듈을 활용하여 `/static` 및 에셋 경로 마운트.
*   **SPA(Single Page Application) 라우팅 처리**: React Router를 사용하는 프론트엔드 특성상, 정의되지 않은 모든 경로는 `index.html`로 리다이렉트하는 Fallback 핸들러 구현.

### 3.3 개발/운영 환경 이원화
*   **Development**: 실시간 코드 반영을 위해 기존처럼 `Vite Dev Server` 활용.
*   **Production**: 빌드된 결과물을 Python 엔진이 실행하여 배포 환경 안정성 확보.

## 4. 리스크 및 대응 방안 (Risk Assessment)

| 리스크 항목 | 내용 및 영향 | 대응 방안 |
|:--- |:--- |:--- |
| **빌드 오버헤드** | UI 수정 시마다 빌드가 필요한 번거로움 | 개발 모드와 운영 모드를 분리하는 환경 변수 도입 |
| **라우팅 충돌** | API 경로와 프론트엔드 페이지 경로의 혼선 | 모든 API는 `/api/` 접두사를 강제하여 경로 격리 |
| **정적 자원 캐싱** | 파일 업데이트 시 브라우저에 구버전이 남는 현상 | Vite의 Content Hash 기반 파일명 생성 기능 활용 |

## 5. 기대 효과 (Expected Benefits)
1.  **배포 단순화**: 컨테이너화(Docker) 시 단일 프로세스만 관리하면 되므로 GCP 배포 난이도 하락.
2.  **성능 향상**: Vite의 프로덕션 빌드 적용으로 리소스 로딩 속도 및 렌더링 최적화.
3.  **보안 강화**: 동일 도메인 정책(Same-Origin Policy) 적용으로 인한 API 보안성 향상.

---
**작성일**: 2026-02-05
**상태**: Draft (Phase 1.5 Milestone)
