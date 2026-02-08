#!/bin/bash
# restart_trade.sh (트레이드 서버 리스타트)
echo "--- [Trade] Restarting Trading Backend (Port 7777) ---"
pkill -f run_server.py
sleep 1
echo "Building Frontend..."
cd trade-front && npm run build && cd ..
export PYTHONPATH=$PYTHONPATH:.
nohup /usr/bin/python3 run_server.py > server.log 2>&1 &
echo "✅ Trading Backend is starting. (Check with: tail -f server.log)"
