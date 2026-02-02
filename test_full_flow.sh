#!/bin/bash
# test_full_flow.sh: TrendHunter 초기화부터 리포트까지 원스톱 테스트

echo "==========================================="
echo " 🚀 TrendHunter Full Flow Test Start"
echo "==========================================="

# 1. 초기화
echo "Step 1: Cleaning & Initializing DB..."
rm -f TrendHunter/db/stock_info.db
python3 run.py init > /dev/null
python3 run.py sync > /dev/null
python3 run.py themes > /dev/null
python3 run.py views > /dev/null
echo "✅ Init Complete."

# 2. 시세 수집 (1분 맛보기)
echo "Step 2: Fetching Daily Prices (Sampling for 40s)..."
# 백그라운드 실행
python3 -u run.py daily > fetch_daily_test.log 2>&1 &
PID_DAILY=$!
sleep 40
kill -2 $PID_DAILY 2>/dev/null # SIGINT로 부드럽게 종료 시도
wait $PID_DAILY 2>/dev/null
echo "✅ Daily Price Sampling Complete."

# 3. 펀더멘털 & 배당 & 수급 채우기 (수집된 종목 대상)
echo "Step 3: Fetching Fundamentals, Dividend, Supply..."
# 수집된 종목만 대상으로 빠르게 돌리기 위해 스크립트 활용하면 좋지만, 
# 여기서는 run.py 명령어를 짧게 실행 (전수조사는 너무 오래 걸림)

# 3-1. 펀더멘털 (빠름)
python3 run.py fundamentals > /dev/null 2>&1 &
PID_FUND=$!

# 3-2. 배당 (빠름 - mine 대신 dividend-all 사용해봄, 안되면 mine 짧게)
python3 run.py dividend-all > /dev/null 2>&1

# 3-3. 수급 (샘플링된 종목에 대해서만 채우는 로직이 없으므로, 
#       방금 만든 scripts/fetch_specific_supply.py를 활용하여 
#       DB에 있는 종목만 수급을 긁어오도록 동적 처리하면 좋음.
#       일단은 run.py supply를 20초 돌리고 끔)
python3 -u run.py supply > fetch_supply_test.log 2>&1 &
PID_SUPPLY=$!
sleep 20
kill -2 $PID_SUPPLY 2>/dev/null
wait $PID_SUPPLY 2>/dev/null

# 펀더멘털도 종료
kill -2 $PID_FUND 2>/dev/null
wait $PID_FUND 2>/dev/null

echo "✅ Context Data (Fund/Div/Supply) Fetched."

# 4. 분석 및 리포트
echo "Step 4: Analyzing & Reporting..."
python3 run.py rs
python3 run.py screen

echo "==========================================="
echo " 🎉 Test Complete!"
echo "==========================================="
