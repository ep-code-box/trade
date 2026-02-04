#!/bin/bash

# 1. Backend 실행 (Background)
echo "🚀 Starting TrendHunter Backend (FastAPI)..."
python3 -m pip install fastapi uvicorn pandas sqlite3 > /dev/null 2>&1

# 로그 파일을 임시 디렉토리로 이동 (Vite 감시 피하기)
LOG_FILE="/tmp/trendhunter_api.log"
PYTHONPATH=. python3 -m uvicorn src.api:app --port 8000 --reload > "$LOG_FILE" 2>&1 &
BACKEND_PID=$!

# 2. Frontend 실행
echo "🚀 Starting TrendHunter Dashboard (React)..."
cd trade-front

# node_modules가 없으면 설치
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Vite 실행
npm run dev

# 종료 시 백엔드도 같이 종료
kill $BACKEND_PID
