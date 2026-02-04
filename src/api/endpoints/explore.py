from fastapi import APIRouter
import pandas as pd
from src.db import get_connection

router = APIRouter(tags=["explorer"])

@router.get("/explore")
def explore_market(
    page: int = 1, limit: int = 50, sort_by: str = "rs_score", order: str = "desc",
    search: str = "", min_rs: float = 0, min_amount: int = 0, max_disparity: float = 0,
    strict_alignment: bool = False, min_low_dist: float = 0, max_high_dist: float = 0,
    master_rules: bool = False
):
    """전체 시장 데이터 탐색 (Advanced Filters)"""
    try:
        conn = get_connection()
        date_res = conn.execute("SELECT MAX(date) FROM daily_analysis").fetchone()
        latest_date = date_res[0] if date_res else None
        if not latest_date: return {"items": [], "total": 0}

        prev_date_res = conn.execute(f"SELECT date FROM daily_analysis WHERE code='0001' AND date < '{latest_date}' ORDER BY date DESC LIMIT 20, 1").fetchone()
        prev_date = prev_date_res[0] if prev_date_res else '00000000'

        base_query = f"""
            SELECT 
                d.code, m.name, d.close, d.open, d.volume, d.amount,
                d.rs_score, d.sma_20, d.sma_50, d.sma_150, d.sma_200,
                m.market_type, m.stck_fcam as market_cap,
                d.high_52w, d.low_52w, d.volume_sma_50,
                (SELECT d2.sma_200 FROM daily_analysis d2 WHERE d2.code = d.code AND d2.date = ?) as sma_200_prev
            FROM daily_analysis d
            JOIN master_info m ON d.code = m.code
            WHERE d.date = ?
        """
        params = [prev_date, latest_date]

        if search:
            base_query += " AND (m.name LIKE ? OR d.code LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        if min_rs > 0:
            base_query += " AND d.rs_score >= ?"; params.append(min_rs)
        if min_amount > 0:
            base_query += " AND d.amount >= ?"; params.append(min_amount * 1000000)
        if max_disparity > 0:
            base_query += " AND d.sma_200 > 0 AND d.close <= (d.sma_200 * ?)"; params.append(1 + max_disparity/100.0)
        if strict_alignment:
            base_query += " AND d.sma_20 > d.sma_50 AND d.sma_50 > d.sma_200"
        if min_low_dist > 0:
            base_query += " AND d.low_52w > 0 AND d.close >= (d.low_52w * ?)"; params.append(1 + min_low_dist/100.0)
        if max_high_dist > 0:
            base_query += " AND d.high_52w > 0 AND d.close >= (d.high_52w * ?)"; params.append(1 - max_high_dist/100.0)
        if master_rules:
            base_query += " AND d.sma_150 > d.sma_200 AND d.sma_200 > sma_200_prev AND d.volume < (d.volume_sma_50 * 0.8) AND ((m.bsop_prfi > 0 AND m.thtr_ntin > 0) OR (d.rs_score >= 90))"

        count_query = f"SELECT COUNT(*) FROM ({base_query})"
        cursor = conn.cursor()
        total_count = cursor.execute(count_query, params).fetchone()[0]

        order_str = "ASC" if order.lower() == "asc" else "DESC"
        base_query += f" ORDER BY {sort_by} {order_str} LIMIT ? OFFSET ?"
        params.extend([limit, (page - 1) * limit])

        cursor.execute(base_query, params)
        rows = cursor.fetchall()
        results = []
        for r in rows:
            results.append({
                "code": r[0], "name": r[1], "close": r[2],
                "change": round((r[2]-r[3])/r[3]*100, 2) if r[3] > 0 else 0,
                "amount": r[5], "rsScore": r[6] or 0, "marketType": r[11],
                "marketCap": r[12], "volume": r[4]
            })
        conn.close()
        return {"items": results, "total": total_count, "page": page, "limit": limit, "date": latest_date}
    except Exception as e:
        return {"error": str(e)}
