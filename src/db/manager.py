"""DB 초기화 및 연결. 경로는 config에서."""
import sqlite3
import os

from src.config import STOCK_DB_PATH


def get_connection():
    """stock_info.db 연결 반환. 사용 후 conn.close() 호출."""
    os.makedirs(os.path.dirname(STOCK_DB_PATH), exist_ok=True)
    return sqlite3.connect(STOCK_DB_PATH)


def init_dbs():
    """마스터·일봉·섹터 테이블 생성."""
    os.makedirs(os.path.dirname(STOCK_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(STOCK_DB_PATH)
    cursor_stock = conn.cursor()

    cursor_stock.execute('''
        CREATE TABLE IF NOT EXISTS master_info (
            code TEXT PRIMARY KEY,
            stnd_iscd TEXT,
            name TEXT,
            market_type TEXT,
            scrt_grp_cls_code TEXT,
            avls_scal_cls_code TEXT,
            bstp_larg_div_code TEXT,
            bstp_medm_div_code TEXT,
            bstp_smal_div_code TEXT,
            low_current_yn TEXT,
            krx_issu_yn TEXT,
            etp_prod_cls_code TEXT,
            krx100_issu_yn TEXT,
            krx_car_yn TEXT,
            krx_smcn_yn TEXT,
            krx_bio_yn TEXT,
            krx_bank_yn TEXT,
            etpr_undt_objt_co_yn TEXT,
            krx_enrg_chms_yn TEXT,
            krx_stel_yn TEXT,
            short_over_cls_code TEXT,
            krx_medi_cmnc_yn TEXT,
            krx_cnst_yn TEXT,
            krx_scrt_yn TEXT,
            krx_ship_yn TEXT,
            krx_insu_yn TEXT,
            krx_trnp_yn TEXT,
            stck_sdpr INTEGER,
            frml_mrkt_deal_qty_unit INTEGER,
            ovtm_mrkt_deal_qty_unit INTEGER,
            trht_yn TEXT,
            sltr_yn TEXT,
            mang_issu_yn TEXT,
            mrkt_alrm_cls_code TEXT,
            mrkt_alrm_risk_adnt_yn TEXT,
            insn_pbnt_yn TEXT,
            byps_lstn_yn TEXT,
            flng_cls_code TEXT,
            fcam_mod_cls_code TEXT,
            icic_cls_code TEXT,
            marg_rate TEXT,
            crdt_able TEXT,
            crdt_days TEXT,
            prdy_vol INTEGER,
            stck_fcam INTEGER,
            stck_lstn_date TEXT,
            lstn_stcn INTEGER,
            cpfn INTEGER,
            stac_month TEXT,
            po_prc INTEGER,
            prst_cls_code TEXT,
            ssts_hot_yn TEXT,
            stange_runup_yn TEXT,
            krx300_issu_yn TEXT,
            sale_account INTEGER,
            bsop_prfi INTEGER,
            op_prfi INTEGER,
            thtr_ntin INTEGER,
            roe REAL,
            base_date TEXT,
            prdy_avls_scal INTEGER,
            grp_code TEXT,
            co_crdt_limt_over_yn TEXT,
            secu_lend_able_yn TEXT,
            stln_able_yn TEXT,
            mnin_cls_code_yn TEXT,
            sprn_strr_nmix_issu_yn TEXT,
            kospi200_apnt_cls_code TEXT,
            kospi100_issu_yn TEXT,
            kospi50_issu_yn TEXT,
            elw_pblc_yn TEXT,
            kospi_issu_yn TEXT,
            sri_nmix_yn TEXT,
            vntr_issu_yn TEXT,
            invt_alrm_yn TEXT,
            ksq150_nmix_yn TEXT,
            per_stock_dvdn_amt REAL,
            dividend_cycle TEXT,
            dividend_count INTEGER,
            per REAL,
            pbr REAL,
            updated_at TEXT
        )
    ''')

    cursor_stock.execute('''
        CREATE TABLE IF NOT EXISTS daily_analysis (
            date TEXT, code TEXT, open INTEGER, high INTEGER, low INTEGER, close INTEGER, 
            volume INTEGER, amount INTEGER, 
            frgn_net_buy INTEGER, orgn_net_buy INTEGER, prsn_net_buy INTEGER,
            fin_net_buy INTEGER, inv_net_buy INTEGER, pension_net_buy INTEGER, etc_net_buy INTEGER,
            market_cap INTEGER, sma_20 REAL, sma_50 REAL, sma_150 REAL, sma_200 REAL,
            high_52w INTEGER, low_52w INTEGER, rs_score REAL,
            vol_std_10d REAL, vol_std_50d REAL, dividend_yield REAL,
            volume_sma_50 REAL,
            eps REAL, bps REAL, revenue_growth REAL, eps_growth REAL, operating_margin REAL,
            PRIMARY KEY (date, code)
        )
    ''')

    cursor_stock.execute('''
        CREATE TABLE IF NOT EXISTS sectors_themes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            category_type TEXT,
            category_name TEXT,
            source TEXT,
            FOREIGN KEY(code) REFERENCES master_info(code)
        )
    ''')

    cursor_stock.execute('''
        CREATE TABLE IF NOT EXISTS trade_plan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            date TEXT,
            code TEXT,
            name TEXT,
            entry_price INTEGER,
            stop_price INTEGER,
            weight TEXT,
            status TEXT DEFAULT 'READY', -- READY, SUBMITTED, FILLED, CANCELLED, STOPPED
            FOREIGN KEY(code) REFERENCES master_info(code)
        )
    ''')

    cursor_stock.execute('''
        CREATE TABLE IF NOT EXISTS trade_execution (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            code TEXT,
            side TEXT, -- BUY, SELL
            qty INTEGER,
            price INTEGER,
            result_msg TEXT,
            FOREIGN KEY(code) REFERENCES master_info(code)
        )
    ''')

    conn.commit()
    conn.close()
    print("Database schema updated to support full KOSPI/KOSDAQ layouts.")


if __name__ == "__main__":
    init_dbs()
