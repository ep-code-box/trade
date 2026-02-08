#!/bin/bash
# mlx-community/Phi-3.5-mini-instruct-4bit 모델을 메모리에 상주시킴
# 포트 11434 (Ollama 스타일) 또는 기본 8080 사용 가능. 여기선 11434 사용.

echo "--- Starting Resident MLX Model Server ---"
/usr/bin/python3 -m mlx_lm.server --model mlx-community/Phi-3.5-mini-instruct-4bit --port 11434
