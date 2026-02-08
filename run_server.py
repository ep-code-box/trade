"""
[TrendHunter Backend Server]
통합 API 서버 실행 스크립트.
"""
import uvicorn
import os
import sys

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # 포트 설정 (GEMINI.md 지침에 따라 7777 포트 우선 사용)
    port = int(os.environ.get("PORT", 7777))
    
    print(f"Starting TrendHunter API Server on port {port} (Reload Enabled, Host: 0.0.0.0)...")
    
    # 개발 편의성을 위해 다시 reload=True 설정
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=port, reload=True)