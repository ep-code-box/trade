#!/bin/bash

# 1. Backend 실행 (Background)
echo "🚀 Starting TrendHunter Backend (FastAPI)..."
# uvicorn 설치 여부 확인
if ! command -v uvicorn &> /dev/null; then
    echo "Installing backend dependencies..."
    pip install fastapi uvicorn pandas sqlite3
fi
uvicorn run_server:app --reload --port 8000 &
BACKEND_PID=$!

# 2. Frontend 실행
echo "🚀 Starting TrendHunter Dashboard (React)..."
cd dashboard

# node_modules가 없으면 설치
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Vite 실행
npm run dev

# 종료 시 백엔드도 같이 종료
kill $BACKEND_PID
