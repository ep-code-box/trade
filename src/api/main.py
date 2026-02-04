from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from src.api.endpoints import account, stocks, explore, settings

app = FastAPI(title="TrendHunter API Server")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(account.router, prefix="/api")
app.include_router(stocks.router, prefix="/api")
app.include_router(explore.router, prefix="/api")
app.include_router(settings.router, prefix="/api")

@app.get("/api/health")
def health_check():
    return {"status": "ok", "time": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
