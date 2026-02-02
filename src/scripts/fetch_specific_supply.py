
import sys
from src.jobs.fetch_supply_history import fetch_supply_history, update_supply_to_db
from datetime import datetime, timedelta

def fetch_specific_supply(codes):
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
    print(f"Fetching supply for {codes}...")
    for code in codes:
        data = fetch_supply_history(code, start_date, end_date)
        if data:
            update_supply_to_db(code, data)
            print(f"Updated {code}")

if __name__ == "__main__":
    fetch_specific_supply(["000720", "00088K", "000810"])
