
import sqlite3
from src.db import get_connection

def super_restore_dividends():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. 최신 날짜 확인
    cursor.execute("SELECT MAX(date) FROM daily_analysis")
    max_date = cursor.fetchone()[0]
    print(f"대상 날짜: {max_date}")
    
    # 2. 모든 날짜를 뒤져서 종목별로 가장 최근의 유효한 배당 수익률 찾기
    print("전체 이력에서 유효 배당 데이터 추출 중...")
    cursor.execute("""
        SELECT code, dividend_yield 
        FROM daily_analysis 
        WHERE dividend_yield > 0 
        ORDER BY date ASC
    """)
    
    # ASC로 읽으면서 덮어쓰면 결과적으로 가장 최신 날짜의 값이 남음
    dividend_map = {}
    for code, yield_val in cursor.fetchall():
        dividend_map[code] = yield_val
            
    print(f"추출 완료: {len(dividend_map)}개 종목")
    
    if not dividend_map:
        print("경고: 과거 이력에도 배당 정보가 없습니다.")
        return

    # 3. 최신 날짜 업데이트
    update_data = []
    for code, yield_val in dividend_map.items():
        update_data.append((yield_val, max_date, code))
        
    print(f"데이터 복구 시작 ({len(update_data)}건)...")
    cursor.executemany("""
        UPDATE daily_analysis 
        SET dividend_yield = ? 
        WHERE date = ? AND code = ?
    """, update_data)
    
    conn.commit()
    print(f"복구 완료: {cursor.rowcount}행 업데이트됨.")
    conn.close()

if __name__ == "__main__":
    super_restore_dividends()
