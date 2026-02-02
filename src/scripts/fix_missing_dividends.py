
import sqlite3
from src.db import get_connection

def fix_dividend_data():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. 최신 날짜 확인
    cursor.execute("SELECT MAX(date) FROM daily_analysis")
    max_date = cursor.fetchone()[0]
    print(f"최신 날짜: {max_date}")
    
    # 2. 바로 이전 날짜들에서 유효한 배당 수익률 가져오기 (가장 최근값 매핑)
    # 메모리에서 처리하기 위해 딕셔너리로 저장
    print("과거 배당 데이터 로드 중...")
    cursor.execute("""
        SELECT code, dividend_yield 
        FROM daily_analysis 
        WHERE dividend_yield > 0 
        AND date < ?
        ORDER BY date DESC
    """, (max_date,))
    
    dividend_map = {}
    for code, yield_val in cursor.fetchall():
        if code not in dividend_map:
            dividend_map[code] = yield_val
            
    # 3. 최신 날짜의 누락된 데이터 업데이트
    print(f"데이터 복구 시작 (대상 종목: {len(dividend_map)}개)...")
    update_data = []
    for code, yield_val in dividend_map.items():
        update_data.append((yield_val, max_date, code))
        
    cursor.executemany("""
        UPDATE daily_analysis 
        SET dividend_yield = ? 
        WHERE date = ? AND code = ? AND (dividend_yield IS NULL OR dividend_yield = 0)
    """, update_data)
    
    conn.commit()
    print(f"복구 완료: {cursor.rowcount}행 업데이트됨.")
    conn.close()

if __name__ == "__main__":
    fix_dividend_data()
