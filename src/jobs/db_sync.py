"""KOSPI/KOSDAQ 마스터 MST 파싱 후 master_info 적재. 실행: python -m src.jobs.db_sync"""
import os
import pandas as pd
from datetime import datetime

from src.config import ROOT
from src.db import get_connection, init_dbs


def parse_kospi_mst_official(file_path):
    if not os.path.exists(file_path):
        return
    print(f"Parsing KOSPI Master (Official Example Logic): {file_path}")
    tmp_fil1 = file_path + "_part1.tmp"
    tmp_fil2 = file_path + "_part2.tmp"

    wf1 = open(tmp_fil1, mode="w", encoding="cp949")
    wf2 = open(tmp_fil2, mode="w", encoding="cp949")

    with open(file_path, mode="r", encoding="cp949") as f:
        for row in f:
            rf1 = row[0 : len(row) - 228]
            rf1_1, rf1_2, rf1_3 = rf1[0:9].rstrip(), rf1[9:21].rstrip(), rf1[21:].strip()
            wf1.write(rf1_1 + "," + rf1_2 + "," + rf1_3 + "\n")
            wf2.write(row[-228:])

    wf1.close()
    wf2.close()

    part1_columns = ["단축코드", "표준코드", "한글명"]
    df1 = pd.read_csv(tmp_fil1, header=None, names=part1_columns, encoding="cp949")
    field_specs = [
        2, 1, 4, 4, 4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 9, 5, 5, 1, 1, 1, 2, 1, 1, 1, 2, 2, 2, 3, 1, 3, 12, 12, 8, 15, 21, 2, 7, 1, 1, 1, 1, 1, 9, 9, 9, 5, 9, 8, 9, 3, 1, 1, 1,
    ]
    part2_columns = [
        "그룹코드", "시가총액규모", "지수업종대분류", "지수업종중분류", "지수업종소분류",
        "제조업", "저유동성", "지배구조지수종목", "KOSPI200섹터업종", "KOSPI100", "KOSPI50", "KRX", "ETP", "ELW발행", "KRX100",
        "KRX자동차", "KRX반도체", "KRX바이오", "KRX은행", "SPAC", "KRX에너지화학", "KRX철강", "단기과열", "KRX미디어통신", "KRX건설",
        "Non1", "KRX증권", "KRX선박", "KRX섹터_보험", "KRX섹터_운송", "SRI", "기준가", "매매수량단위", "시간외수량단위", "거래정지",
        "정리매매", "관리종목", "시장경고", "경고예고", "불성실공시", "우회상장", "락구분", "액면변경", "증자구분", "증거금비율",
        "신용가능", "신용기간", "전일거래량", "액면가", "상장일자", "상장주수", "자본금", "결산월", "공모가", "우선주",
        "공매도과열", "이상급등", "KRX300", "KOSPI", "매출액", "영업이익", "경상이익", "당기순이익", "ROE", "기준년월",
        "시가총액", "그룹사코드", "회사신용한도초과", "담보대출가능", "대주가능",
    ]
    df2 = pd.read_fwf(tmp_fil2, widths=field_specs, names=part2_columns)
    df = pd.merge(df1, df2, how="outer", left_index=True, right_index=True)
    save_to_db(df, "KOSPI")
    os.remove(tmp_fil1)
    os.remove(tmp_fil2)


def parse_kosdaq_mst_official(file_path):
    if not os.path.exists(file_path):
        return
    print(f"Parsing KOSDAQ Master (Official Example Logic): {file_path}")
    tmp_fil1 = file_path + "_part1.tmp"
    tmp_fil2 = file_path + "_part2.tmp"

    wf1 = open(tmp_fil1, mode="w", encoding="cp949")
    wf2 = open(tmp_fil2, mode="w", encoding="cp949")

    with open(file_path, mode="r", encoding="cp949") as f:
        for row in f:
            rf1 = row[0 : len(row) - 222]
            rf1_1, rf1_2, rf1_3 = rf1[0:9].rstrip(), rf1[9:21].rstrip(), rf1[21:].strip()
            wf1.write(rf1_1 + "," + rf1_2 + "," + rf1_3 + "\n")
            wf2.write(row[-222:])

    wf1.close()
    wf2.close()

    part1_columns = ["단축코드", "표준코드", "한글종목명"]
    df1 = pd.read_csv(tmp_fil1, header=None, names=part1_columns, encoding="cp949")
    field_specs = [
        2, 1, 4, 4, 4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 9, 5, 5, 1, 1, 1, 2, 1, 1, 1, 2, 2, 2, 3, 1, 3, 12, 12, 8, 15, 21, 2, 7, 1, 1, 1, 1, 9, 9, 9, 5, 9, 8, 9, 9, 3, 1, 1, 1,
    ]
    part2_columns = [
        "증권그룹구분코드", "시가총액 규모 구분 코드 유가", "지수업종 대분류 코드", "지수 업종 중분류 코드", "지수업종 소분류 코드", "벤처기업 여부 (Y/N)",
        "저유동성종목 여부", "KRX 종목 여부", "ETP 상품구분코드", "KRX100 종목 여부 (Y/N)", "KRX 자동차 여부", "KRX 반도체 여부", "KRX 바이오 여부", "KRX 은행 여부", "기업인수목적회사여부",
        "KRX 에너지 화학 여부", "KRX 철강 여부", "단기과열종목구분코드", "KRX 미디어 통신 여부", "KRX 건설 여부", "(코스닥)투자주의환기종목여부", "KRX 증권 구분", "KRX 선박 구분",
        "KRX섹터지수 보험여부", "KRX섹터지수 운송여부", "KOSDAQ150지수여부 (Y,N)", "주식 기준가", "정규 시장 매매 수량 단위", "시간외 시장 매매 수량 단위", "거래정지 여부", "정리매매 여부",
        "관리 종목 여부", "시장 경고 구분 코드", "시장 경고위험 예고 여부", "불성실 공시 여부", "우회 상장 여부", "락구분 코드", "액면변경 구분 코드", "증자 구분 코드", "증거금 비율",
        "신용주문 가능 여부", "신용기간", "전일 거래량", "주식 액면가", "주식 상장 일자", "상장 주수(천)", "자본금", "결산 월", "공모 가격", "우선주 구분 코드", "공매도과열종목여부", "이상급등종목여부",
        "KRX300 종목 여부 (Y/N)", "매출액", "영업이익", "경상이익", "단기순이익", "ROE(자기자본이익률)", "기준년월", "전일기준 시가총액 (억)", "그룹사 코드", "회사신용한도초과여부", "담보대출가능여부", "대주가능여부",
    ]
    df2 = pd.read_fwf(tmp_fil2, widths=field_specs, names=part2_columns)
    df = pd.merge(df1, df2, how="outer", left_index=True, right_index=True)
    save_to_db(df, "KOSDAQ")
    os.remove(tmp_fil1)
    os.remove(tmp_fil2)


def save_to_db(df, market_type):
    mapping = {
        "단축코드": "code", "표준코드": "stnd_iscd", "한글명": "name", "한글종목명": "name",
        "증권그룹구분코드": "scrt_grp_cls_code", "지수업종대분류": "bstp_larg_div_code",
        "지수업종중분류": "bstp_medm_div_code", "지수업종소분류": "bstp_smal_div_code",
        "지수업종 대분류 코드": "bstp_larg_div_code", "지수 업종 중분류 코드": "bstp_medm_div_code",
        "지수업종 소분류 코드": "bstp_smal_div_code",
        "매출액": "sale_account", "영업이익": "bsop_prfi", "경상이익": "op_prfi",
        "당기순이익": "thtr_ntin", "단기순이익": "thtr_ntin", "ROE": "roe", "ROE(자기자본이익률)": "roe",
    }
    df_db = df.rename(columns=mapping)
    df_db["market_type"] = market_type
    df_db["updated_at"] = datetime.now().strftime("%Y-%m-%d")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(master_info)")
    db_cols = [row[1] for row in cur.fetchall()]
    final_cols = [c for c in df_db.columns if c in db_cols]
    df_db[final_cols].to_sql("master_info", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()
    print(f"Saved {len(df_db)} {market_type} records.")


if __name__ == "__main__":
    init_dbs()
    conn = get_connection()
    conn.execute("DELETE FROM master_info")
    conn.commit()
    conn.close()

    parse_kospi_mst_official(os.path.join(ROOT, "kospi_code.mst"))
    parse_kosdaq_mst_official(os.path.join(ROOT, "kosdaq_code.mst"))
