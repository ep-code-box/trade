
import sqlite3
import pandas as pd
import json
import os
import sys

def get_connection():
    return sqlite3.connect('TrendHunter/db/stock_info.db')

def get_basket():
    try:
        conn = get_connection()
        query = """
            WITH target_symbols AS (
                SELECT symbol FROM basket
                UNION
                SELECT code as symbol FROM trade_plan WHERE status = 'MONITORING'
                UNION
                SELECT symbol FROM account_positions_audit WHERE qty > 0
            ),
            latest_plan AS (
                SELECT code, name, entry_price, stop_price, status,
                       ROW_NUMBER() OVER (PARTITION BY code ORDER BY (CASE WHEN status = 'MONITORING' THEN 0 WHEN status = 'ORDERED' THEN 1 ELSE 2 END), date DESC, id DESC) as rn
                FROM trade_plan
            ),
            latest_price AS (
                SELECT code, close, ROW_NUMBER() OVER (PARTITION BY code ORDER BY date DESC) as rn
                FROM daily_analysis
            )
            SELECT 
                s.symbol,
                COALESCE(p.name, b.name, s.symbol) as name,
                COALESCE(p.entry_price, b.target_price) as targetPrice,
                COALESCE(p.stop_price, b.stop_price) as stopLossPrice,
                CASE 
                    WHEN COALESCE(a.qty, 0) > 0 THEN 'BOUGHT'
                    WHEN p.status = 'MONITORING' THEN 'MONITORING'
                    ELSE 'READY'
                END as status,
                pr.close as price,
                COALESCE(a.qty, 0) as current_qty
            FROM target_symbols s
            LEFT JOIN basket b ON s.symbol = b.symbol
            LEFT JOIN account_positions_audit a ON s.symbol = a.symbol
            LEFT JOIN latest_plan p ON s.symbol = p.code AND p.rn = 1
            LEFT JOIN latest_price pr ON s.symbol = pr.code AND pr.rn = 1
            WHERE s.symbol IS NOT NULL
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.to_dict(orient='records')
    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()}

if __name__ == "__main__":
    res = get_basket()
    print(json.dumps(res, indent=2, ensure_ascii=False))
