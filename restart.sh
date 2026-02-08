#!/bin/bash

echo "--- [1/2] Killing existing server processes ---"
pkill -f run_server.py
sleep 1

echo "--- [2/2] Starting Backend Server (Python 3.9) ---"
# PYTHONPATH를 강제로 현재 디렉토리로 설정
# Reload를 끄고 포그라운드에서 실행하는 것과 유사하게 nohup 사용
export PYTHONPATH=$PYTHONPATH:.
nohup /usr/bin/python3 run_server.py > server.log 2>&1 &
echo $! > server.pid

echo "✅ Restart Complete! Checking logs..."
sleep 3
tail -n 20 server.log