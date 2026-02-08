#!/bin/bash
# restart_llm.sh (만수르 엔진 리스타트)
echo "--- [AI/Mansour] Restarting Model Server with Llama-3.1-8B (The Smart One) ---"
lsof -ti:11434 | xargs kill -9 2>/dev/null
sleep 1
# 8B 모델은 메모리를 더 사용하지만 훨씬 똑똑합니다.
nohup /usr/bin/python3 -m mlx_lm.server --model mlx-community/Llama-3.1-8B-Instruct-4bit --port 11434 > llm_server.log 2>&1 &
echo "✅ AI Model Server is loading Llama-3.1-8B. (Check with: tail -f llm_server.log)"
