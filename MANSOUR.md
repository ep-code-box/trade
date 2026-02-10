# 🧠 MANSOUR Engine (Hybrid AI Architecture)

## 1. Overview
**Mansour(만수르)**는 TrendHunter의 통합 AI 전략 엔진입니다. 
2026년 현재 **Google Gemini 3 Flash**를 주력 분석기로 사용하며, 시스템 리소스 및 할당량 문제 발생 시 **로컬 MLX 모델 (Llama-3.1-8B)**로 자동 전환될 수 있는 하이브리드 구조를 지향합니다.

## 2. Analytical Philosophy (Core Rules)
모든 AI 분석은 다음의 **'사자의 눈'** 원칙을 반드시 준수해야 합니다:
1.  **구조 우선 (Structure First)**: 단순 가격이 아닌 VCP(변동성 수축)와 이평선 정배열(Stage 2)을 분석의 핵심 근거로 삼는다.
2.  **데이터 증거 (Market Evidence)**: RS Score, 조정 깊이, 거래량 마름(VDU) 수치를 반드시 인용한다.
3.  **사냥꾼의 결론**: 모호한 조언을 배제하고 `BUY(진입)`, `READY(매복)`, `SKIP(제외)` 중 하나를 단호하게 판결한다.

## 3. Operational Flow
1.  **Trigger**: 사용자가 대시보드에서 [AI 분석] 버튼 클릭.
2.  **Execution**: 
    - 백엔드에서 Google Gemini 3 Flash API 호출 및 결과 생성.
    - 결과 생성 즉시 **텔레그램 봇**을 통해 사용자에게 리포트 전송.
3.  **Fallback**: 클라우드 API 실패 시 로컬 상주 서버(`Port 11434`)를 통해 분석 수행.

## 4. Maintenance
- **API Key**: `system_config` 테이블의 `th_ai_config`에서 관리.
- **Local Server**: `restart_llm.sh` (상위 폴더 관리)를 통해 Llama-3.1-8B 상주 기동.
- **Frontend Sync**: `geminiService.ts`에서 백엔드 API(`/api/stocks/.../ai-analysis`) 호출.