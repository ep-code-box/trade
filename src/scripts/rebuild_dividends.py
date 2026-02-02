
import sqlite3
from src.db import get_connection

def rebuild_dividend_yield():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. 최신 날짜 확인
    cursor.execute("SELECT MAX(date) FROM daily_analysis")
    max_date = cursor.fetchone()[0]
    
    # 2. master_info에서 주당배당금(per_stock_dvdn_amt) 가져오기
    print("배당금 정보 로드 중...")
    cursor.execute("SELECT code, per_stock_dvdn_amt FROM master_info WHERE per_stock_dvdn_amt > 0")
    dps_map = dict(cursor.fetchall())
    
    # 3. 최신 날짜의 현재가(close) 가져오기
    print(f"{max_date} 시세 데이터 로드 중...")
    cursor.execute("SELECT code, close FROM daily_analysis WHERE date = ?", (max_date,))
    price_data = cursor.fetchall()
    
    # 4. 배당수익률 계산 및 업데이트 리스트 생성
    print("배당수익률 재계산 중...")
    update_data = []
    for code, close in price_data:
        if code in dps_map and close > 0:
            dvdn_yield = (dps_map[code] / close) * 100
            update_data.append((dvdn_yield, max_date, code))
            
    # 5. 대량 업데이트
    print(f"데이터 반영 중 ({len(update_data)}건)...")
    cursor.executemany("""
        UPDATE daily_analysis 
        SET dividend_yield = ? 
        WHERE date = ? AND code = ?
    """, update_data)
    
    conn.commit()
    print(f"완료: {cursor.rowcount}개 종목의 배당 정보가 최신화되었습니다.")
    conn.close()

if __name__ == "__main__":
    rebuild_dividend_yield()
