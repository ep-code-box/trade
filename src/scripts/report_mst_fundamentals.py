
import pandas as pd
from src.db import get_connection

def report_mst_health():
    conn = get_connection()
    targets = ["005930", "005380", "088350"] # 삼성전자, 현대차, 한화생명
    
    query = f"""
    SELECT code, name, stck_sdpr, flng_cls_code, sale_account, bsop_prfi, thtr_ntin, roe, stck_fcam, lstn_stcn
    FROM master_info
    WHERE code IN ({','.join(['?' for _ in targets])})
    """
    df = pd.read_sql_query(query, conn, params=targets)
    conn.close()

    print("\n" + "=" * 80)
    print(" [TrendHunter] MST 기반 종목 기초 체력 보고서 (Data Audit)")
    print("=" * 80)
    
    lock_desc = {"00": "정상", "01": "권리락", "02": "배당락", "03": "분할락", "04": "병합락"}

    for _, row in df.iterrows():
        lock_status = lock_desc.get(str(row['flng_cls_code']).zfill(2), "알수없음")
        print(f"\n▶ [{row['name']} ({row['code']})]")
        print(f"   - 상태: {lock_status} (락구분:{row['flng_cls_code']}) | 기준가: {row['stck_sdpr']:,}원 | 액면가: {row['stck_fcam']:,}원")
        print(f"   - 재무: 매출 {row['sale_account']:,}억 | 영업익 {row['bsop_prfi']:,}억 | 당기순익 {row['thtr_ntin']:,}억")
        print(f"   - 효율: ROE {row['roe']:.2f}% | 상장주수 {row['lstn_stcn']:,}주")
        
        # 오닐의 필터: 흑자 여부 체크
        if row['thtr_ntin'] > 0:
            print("   ✅ [합격] 당기순이익 흑자 유지 중.")
        else:
            print("   🚨 [경고] 당기순이익 적자! 기초 체력 주의.")

    print("\n" + "=" * 80)
    print(" [AI 멘토의 조언] 숫자는 거짓말을 하지 않습니다. 락구분(Dividend Lock) 정보를 통해 차트 왜곡을 피하십시오.")

if __name__ == "__main__":
    report_mst_health()
