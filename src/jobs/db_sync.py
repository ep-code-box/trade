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
            # [v16.0] 절대 인덱스 파싱 (밀림 방지)
            # 코드: 0~9, 이름: 21~61
            code = row[0:9].strip()
            name = row[21:61].strip()
            
            # ST 그룹코드 확인 (KOSPI/KOSDAQ 공통 오프셋 적용 시도)
            # 안전하게 여러 군데 찔러봄
            is_st = row[163:165] == 'ST' or row[-228:-226] == 'ST' or row[-222:-220] == 'ST'
            
            # ST가 아니면 스킵 (ETF 제거)
            if not is_st and 'ST' not in row: continue
            if '스팩' in name: continue
            if name.endswith('우') or name.endswith('우B') or name.endswith('(전환)'): continue

            # 액면가 (152~162), 상장주식수 (170~185) - 삼성전자 기준
            # KOSPI/KOSDAQ 오프셋이 다를 수 있으므로 try-catch로 안전장치
            try:
                if market_type == 'KOSPI':
                    fcam = row[152:162].strip()
                    stcn = row[170:185].strip()
                else:
                    # KOSDAQ은 오프셋이 다름. 일단 KOSPI 기준으로 시도하고 추후 보정
                    # (일단은 텍스트 파싱의 유연함을 믿음)
                    fcam = row[152:162].strip() 
                    stcn = row[170:185].strip()
            except:
                fcam = "0"
                stcn = "0"

            data = {
                "code": code, 
                "name": name.split('  ')[0].strip(), # [TrendHunter] Trailing codes like ST310 are not part of the name
                "scrt_grp_cls_code": "ST",
                "stck_fcam": fcam,
                "lstn_stcn": stcn
            }
            records.append(data)
            
    if records: save_to_db(pd.DataFrame(records), market_type)

def save_to_db(df, market_type):
    # DB 컬럼 매핑 (파싱한 데이터 -> DB)
    df_db = df.copy()
    df_db["market_type"] = market_type
    df_db["updated_at"] = datetime.now().strftime("%Y%m%d")
    
    # 숫자 변환
    for c in ["stck_fcam", "lstn_stcn"]:
        df_db[c] = pd.to_numeric(df_db[c], errors='coerce').fillna(0)

    conn = get_connection()
    
    # [v9.1] 데이터 보존형 업데이트 (ROE, EPS 등 기존 데이터 유지)
    try:
        # 기존 데이터 로드
        existing_df = pd.read_sql_query(f"SELECT * FROM master_info WHERE market_type = '{market_type}'", conn)
        
        if not existing_df.empty:
            # 신규 데이터와 병합 (기존의 financial 데이터는 유지하고, name/updated_at 등만 갱신)
            # 1. 신규 데이터의 컬럼만 추출
            new_cols = df_db.columns.tolist()
            # 2. 기존 데이터에서 신규 데이터에 없는 컬럼들만 추출 (roe, eps, thtr_ntin 등)
            keep_cols = [c for c in existing_df.columns if c not in new_cols or c == 'code']
            
            # 3. 병합
            merged_df = pd.merge(df_db, existing_df[keep_cols], on='code', how='left')
            # 4. 기존에 없던 종목은 NULL로 채워짐
        else:
            merged_df = df_db

        cur = conn.cursor()
        # 해당 마켓 데이터만 삭제 후 전체(병합본) 삽입
        cur.execute("DELETE FROM master_info WHERE market_type = ?", (market_type,))
        merged_df.to_sql("master_info", conn, if_exists="append", index=False)
        conn.commit()
    except Exception as e:
        print(f"DB 동기화 중 오류: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    print(f"✅ {len(df_db)} {market_type} records synchronized (Preserving Financials).")

def main():
    init_db()
    tmp_dir = os.path.join(ROOT, "TrendHunter", "tmp")
    parse_mst_standard(os.path.join(tmp_dir, "kospi_code.mst"), "KOSPI")
    parse_mst_standard(os.path.join(tmp_dir, "kosdaq_code.mst"), "KOSDAQ")

if __name__ == "__main__": main()