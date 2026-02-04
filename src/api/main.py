from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from datetime import datetime
import os
from src.api.endpoints import account, stocks, explore, settings, basket

app = FastAPI(title="TrendHunter API Server")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(account.router, prefix="/api")
app.include_router(stocks.router, prefix="/api")
app.include_router(explore.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(basket.router, prefix="/api")

# [v6.7] 빌드된 프론트엔드 정적 파일 서빙
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "trade-front", "dist")

if os.path.exists(FRONTEND_DIST):
    # API 경로를 제외한 모든 경로를 프론트엔드 정적 파일로 연결
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # API 요청은 라우터에서 먼저 처리되므로, 여기는 그 외의 모든 경로(SPA 라우팅 포함) 처리
        if full_path.startswith("api"):
            return None # 라우터로 전달
        
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

@app.get("/api/health")
def health_check():
    return {"status": "ok", "time": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
