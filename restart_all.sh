#!/bin/bash
# restart_all.sh (통합 지능형 리스타트)

echo "--- [Check] Checking AI Model Server Health ---"
# 11434 포트가 응답하는지 체크 (Health Check)
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:11434/v1/models || echo "000")

if [ "$HTTP_STATUS" == "200" ]; then
    echo "✅ AI Model Server is already running and healthy."
else
    echo "⚠️ AI Model Server not responding (Status: $HTTP_STATUS). Starting it now..."
    ./restart_llm.sh
    echo "Waiting for Model to load (approx 15s)..."
    sleep 15
fi

# 트레이드 서버 재기동
./restart_trade.sh

echo "🚀 All systems are being orchestrated!"
