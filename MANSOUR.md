# 🧠 MANSOUR Engine (Local AI Architecture)

## 1. Overview
**Mansour(만수르)**는 TrendHunter의 핵심 두뇌 역할을 하는 로컬 LLM 서비스 엔진입니다. Apple Silicon의 GPU를 활용하는 MLX 프레임워크를 기반으로 하며, 독립적인 상주 프로세스로 운영됩니다.

## 2. Core Rules (Mandatory)
1.  **독립 운영**: AI 엔진은 반드시 `Port 11434`에서 별도 프로세스로 가동되어야 한다.
2.  **모델 사양**: 기본 모델은 `mlx-community/Phi-3.5-mini-instruct-4bit`를 사용한다. (3.8B 파라미터로 논리력과 속도의 균형 최적화)
3.  **상태 보존**: 백엔드 API 서버(`Port 7777`)를 재기동하더라도 AI 엔진 프로세스는 종료하지 않는다.
4.  **분석 프로토콜**:
    *   모든 분석 요청은 `src/utils/mlx_llm.py` 클라이언트를 통해서 수행한다.
    *   분석 데이터 전달 시 반드시 `JSON` 직렬화를 사용하며, 수치 데이터 누락을 금지한다.

## 3. Operational Scripts
*   `restart_llm.sh`: AI 모델 서버만 단독 재기동 (메모리 리프레시 필요 시).
*   `restart_trade.sh`: 트레이딩 백엔드/프론트엔드만 재기동 (코드 수정 시).
*   `restart_all.sh`: 전체 시스템 통합 지능형 기동 (모델 서버 상태 체크 후 기동).

## 4. Troubleshooting
*   **Response Timeout**: 모델 로딩 중일 가능성이 높음. `llm_server.log`를 확인하여 `Application startup complete` 메시지를 확인한다.
*   **Import Error**: `mlx-lm` 패키지가 설치된 Python 환경(`/usr/bin/python3`)에서 실행 중인지 확인한다.
