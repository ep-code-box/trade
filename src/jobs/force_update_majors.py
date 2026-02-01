"""주요 종목의 OHLCV 데이터를 강제 업데이트하여 DB를 복구합니다."""
import time
from src.jobs.fetch_daily_price import fetch_price_history, process_and_save
from datetime import datetime, timedelta

# 리포트에 나왔던 주요 종목 + 잠재적 후보군
target_codes = [
    "090360", "006910", "170920", "166090", "200710", "119500", "131290", # Track 1
    "008830", "094820", "023160", "014620", "083450", 
    "397030", "003380", "027360", "365270", "156100", # Leaders
    "126340", "389030", "299170", "298830", # Track EX
    "415380", "039130", "092130", "194370", "005830", "067280" # Track 2
]

def update_major_stocks():
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d") # 1년치
    
    print(f"주요 종목 {len(target_codes)}개 데이터 긴급 복구 중 ({start_date} ~ {end_date})...")
    
    for idx, code in enumerate(target_codes):
        print(f"[{idx+1}/{len(target_codes)}] Updating {code}...", end="\r")
        data = fetch_price_history(code, start_date, end_date)
        if data:
            # process_and_save는 이제 open, high, low를 포함해서 저장함
            process_and_save(code, data)
        time.sleep(0.1) # API 부하 조절
        
    print("\n업데이트 완료. 이제 지표를 재계산하세요.")

if __name__ == "__main__":
    update_major_stocks()
