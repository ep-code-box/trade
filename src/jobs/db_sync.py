# -*- coding: utf-8 -*-
"""
[v9.0] 스승님의 지침 기반 '공식 정석' 마스터 파서 (성공본)
기능: KIS 공식 슬라이싱(row[-228:]) 및 공식 field_specs 완벽 적용
실행: python -m src.jobs.db_sync
"""
import os
import pandas as pd
from datetime import datetime
from src.config import ROOT
from src.db import get_connection, init_db

def parse_mst_standard(file_path, market_type):
    if not os.path.exists(file_path): return
    print(f"🚀 {market_type} 마스터 공식 정석 파싱 시작...")
    
    if market_type == "KOSPI":
        p2_len = 228
        field_specs = [2, 1, 4, 4, 4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 9, 5, 5, 1, 1, 1, 2, 1, 1, 1, 2, 2, 2, 3, 1, 3, 12, 12, 8, 15, 21, 2, 7, 1, 1, 1, 1, 1, 9, 9, 9, 5, 9, 8, 9, 3, 1, 1, 1]
        columns = ['그룹코드', '시가총액규모', '지수업종대분류', '지수업종중분류', '지수업종소분류', '제조업', '저유동성', '지배구조지수종목', 'KOSPI200섹터업종', 'KOSPI100', 'KOSPI50', 'KRX', 'ETP', 'ELW발행', 'KRX100', 'KRX자동차', 'KRX반도체', 'KRX바이오', 'KRX은행', 'SPAC', 'KRX에너지화학', 'KRX철강', '단기과열', 'KRX미디어통신', 'KRX건설', 'Non1', 'KRX증권', 'KRX선박', 'KRX섹터_보험', 'KRX섹터_운송', 'SRI', '기준가', '매매수량단위', '시간외수량단위', '거래정지', '정리매매', '관리종목', '시장경고', '경고예고', '불성실공시', '우회상장', '락구분', '액면변경', '증자구분', '증거금비율', '신용가능', '신용기간', '전일거래량', '액면가', '상장일자', '상장주수', '자본금', '결산월', '공모가', '우선주', '공매도과열', '이상급등', 'KRX300', 'KOSPI', '매출액', '영업이익', '경상이익', '당기순이익', 'ROE', '기준년월', '시가총액', '그룹사코드', '회사신용한도초과', '담보대출가능', '대주가능']
    else: # KOSDAQ
        p2_len = 222
        field_specs = [2, 1, 4, 4, 4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 9, 5, 5, 1, 1, 1, 2, 1, 1, 1, 2, 2, 2, 3, 1, 3, 12, 12, 8, 15, 21, 2, 7, 1, 1, 1, 1, 9, 9, 9, 5, 9, 8, 9, 9, 3, 1, 1, 1]
        columns = ['증권그룹구분코드', '시가총액규모코드', '지수업종대분류코드', '지수업종중분류코드', '지수업종소분류코드', '벤처기업여부', '저유동성종목여부', 'KRX종목여부', 'ETP상품구분코드', 'KRX100종목여부', 'KRX자동차여부', 'KRX반도체여부', 'KRX바이오여부', 'KRX은행여부', '기업인수목적회사여부', 'KRX에너지화학여부', 'KRX철강여부', '단기과열종목구분코드', 'KRX미디어통신여부', 'KRX건설여부', '투자주의환기종목여부', 'KRX증권구분', 'KRX선박구분', 'KRX섹터지수보험여부', 'KRX섹터지수운송여부', 'KOSDAQ150지수여부', '기준가', '정규시장매매수량단위', '시간외시장매매수량단위', '거래정지여부', '정리매매여부', '관리종목여부', '시장경고구분코드', '시장경고위험예고여부', '불성실공시여부', '우회상장여부', '락구분코드', '액면가변경구분코드', '증자구분코드', '증거금비율', '신용주문가능여부', '신용기간', '전일거래량', '주식액면가', '주식상장일자', '상장주수', '자본금', '결산월', '공모가격', '우선주구분코드', '공매도과열종목여부', '이상급등종목여부', 'KRX300종목여부', '매출액', '영업이익', '경상이익', '당기순이익', 'ROE', '기준년월', '시가총액', '그룹사코드', '회사신용한도초과여부', '담보대출가능여부', '대주가능여부']

    records = []
    with open(file_path, mode="r", encoding="cp949") as f:
        for row in f:
            part2 = row[-p2_len-1:-1]
            part1 = row[0:len(row)-p2_len-1]
            data = {"code": part1[0:9].strip(), "name": part1[21:].strip()}
            curr = 0
            for w, col in zip(field_specs, columns):
                data[col] = part2[curr:curr+w].strip()
                curr += w
            records.append(data)
            
    if records: save_to_db(pd.DataFrame(records), market_type)

def save_to_db(df, market_type):
    mapping = {
        "기준가": "stck_sdpr", "락구분": "flng_cls_code", "락구분코드": "flng_cls_code",
        "액면가": "stck_fcam", "주식액면가": "stck_fcam", "상장주수": "lstn_stcn", 
        "자본금": "cpfn", "결산월": "stac_month", "매출액": "sale_account", 
        "영업이익": "bsop_prfi", "경상이익": "op_prfi", "당기순이익": "thtr_ntin", "ROE": "roe"
    }
    df_db = df.rename(columns=mapping)
    df_db["market_type"] = market_type
    df_db["updated_at"] = datetime.now().strftime("%Y%m%d")

    def clean_val(val, is_roe=False):
        try:
            s = str(val).strip()
            if not s or s == "nan": return 0.0
            # [보정] ROE에만 날짜 접두어 제거 적용
            if is_roe and len(s) > 6 and '.' not in s[:6]: return float(s[6:])
            return float(s)
        except: return 0.0

    numeric_cols = ["stck_sdpr", "stck_fcam", "lstn_stcn", "cpfn", "sale_account", "bsop_prfi", "op_prfi", "thtr_ntin"]
    for c in numeric_cols:
        if c in df_db.columns: df_db[c] = df_db[c].apply(lambda x: clean_val(x, False))
    
    if 'roe' in df_db.columns:
        df_db['roe'] = df_db['roe'].apply(lambda x: clean_val(x, True))

    conn = get_connection()
    cur = conn.cursor()
    cur.executemany("DELETE FROM master_info WHERE code = ?", [(c,) for c in df_db['code'].tolist()])
    cur.execute("PRAGMA table_info(master_info)")
    db_cols = [row[1] for row in cur.fetchall()]
    final_cols = [c for c in df_db.columns if c in db_cols]
    df_db[final_cols].to_sql("master_info", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()
    print(f"✅ {len(df_db)} {market_type} records synchronized.")

def main():
    init_db()
    tmp_dir = os.path.join(ROOT, "TrendHunter", "tmp")
    parse_mst_standard(os.path.join(tmp_dir, "kospi_code.mst"), "KOSPI")
    parse_mst_standard(os.path.join(tmp_dir, "kosdaq_code.mst"), "KOSDAQ")

if __name__ == "__main__": main()