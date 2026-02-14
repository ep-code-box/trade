#!/bin/bash
# run_all_bots.sh: 모든 매매 관련 봇 통합 실행 스크립트

BASE_DIR="/Users/lastep/Code/trade"
cd $BASE_DIR
export PYTHONPATH=$BASE_DIR

# 1. 기존 봇 정리
echo "Cleaning up existing bot processes..."
pkill -9 -f "src.jobs.trade_bot" || true
pkill -9 -f "src.jobs.trade_bot_server" || true
pkill -9 -f "src.utils.bot_listener" || true

# 2. 로그 디렉토리 확인
mkdir -p logs

# 3. 실시간 매매 봇 실행 (로컬 감시 및 시장가 대응)
echo "Starting TradeBot (Local)..."
nohup ./venv/bin/python3 -u -m src.jobs.trade_bot > logs/trade_bot.log 2>&1 &

# 4. 서버 자동 주문 봇 실행 (KIS 서버 예약 감시)
echo "Starting ServerTradeBot (KIS Server)..."
nohup ./venv/bin/python3 -u -m src.jobs.trade_bot_server > logs/trade_server_bot.log 2>&1 &

# 5. 텔레그램 봇 리스너 실행
echo "Starting Bot Listener (Telegram)..."
nohup ./venv/bin/python3 -u -m src.utils.bot_listener > logs/bot_listener.log 2>&1 &

echo "All bots started. Check logs/ directory for status."
ps aux | grep -E "trade_bot|bot_listener" | grep -v grep
