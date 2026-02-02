"""DB 스키마 관리 모듈: 테이블 생성 및 초기화."""
import sqlite3
import os

DB_PATH = "TrendHunter/db/stock_info.db"

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # 1. 마스터 정보 (종목 기본 정보 + 재무 지표)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS master_info (
            code TEXT PRIMARY KEY,          -- 단축코드 (PK)
            stnd_iscd TEXT,                 -- 표준코드
            name TEXT,                      -- 한글종목명
            market_type TEXT,               -- KOSPI / KOSDAQ
            
            -- [기본 정보]
            scrt_grp_cls_code TEXT,         -- 증권그룹구분코드
            avls_scal_cls_code TEXT,        -- 시가총액 규모 구분
            bstp_larg_div_code TEXT,        -- 지수 업종 대분류
            bstp_medm_div_code TEXT,        -- 지수 업종 중분류
            bstp_smal_div_code TEXT,        -- 지수 업종 소분류
            
            -- [상태 플래그]
            low_current_yn TEXT,            -- 저유동성종목 여부
            krx_issu_yn TEXT,               -- KRX 종목 여부
            etp_prod_cls_code TEXT,         -- ETP 상품구분코드
            krx100_issu_yn TEXT,            -- KRX100 종목 여부
            krx_car_yn TEXT,                -- KRX 자동차
            krx_smcn_yn TEXT,               -- KRX 반도체
            krx_bio_yn TEXT,                -- KRX 바이오
            krx_bank_yn TEXT,               -- KRX 은행
            etpr_undt_objt_co_yn TEXT,      -- 기업인수목적회사
            krx_enrg_chms_yn TEXT,          -- KRX 에너지 화학
            krx_stel_yn TEXT,               -- KRX 철강
            short_over_cls_code TEXT,       -- 단기과열종목구분
            krx_medi_cmnc_yn TEXT,          -- KRX 미디어 통신
            krx_cnst_yn TEXT,               -- KRX 건설
            krx_scrt_yn TEXT,               -- KRX 증권
            krx_ship_yn TEXT,               -- KRX 선박
            krx_insu_yn TEXT,               -- KRX 보험
            krx_trnp_yn TEXT,               -- KRX 운송
            trht_yn TEXT,                   -- 거래정지 여부
            sltr_yn TEXT,                   -- 정리매매 여부
            mang_issu_yn TEXT,              -- 관리 종목 여부
            mrkt_alrm_cls_code TEXT,        -- 시장 경고 구분
            mrkt_alrm_risk_adnt_yn TEXT,    -- 시장 경고위험 예고
            insn_pbnt_yn TEXT,              -- 불성실 공시 여부
            byps_lstn_yn TEXT,              -- 우회 상장 여부
            flng_cls_code TEXT,             -- 락구분 코드 (01:권리락, 02:배당락...)
            fcam_mod_cls_code TEXT,         -- 액면가 변경 구분
            icic_cls_code TEXT,             -- 증자 구분
            crdt_able TEXT,                 -- 신용주문 가능 여부
            ssts_hot_yn TEXT,               -- 공매도과열종목
            stange_runup_yn TEXT,           -- 이상급등종목
            krx300_issu_yn TEXT,            -- KRX300 종목
            
            -- [가격/재무 정보]
            stck_sdpr INTEGER,              -- 주식 기준가 (배당락 전 보정용)
            frml_mrkt_deal_qty_unit INTEGER,-- 정규 시장 매매 수량 단위
            ovtm_mrkt_deal_qty_unit INTEGER,-- 시간외 시장 매매 수량 단위
            marg_rate TEXT,                 -- 증거금 비율
            crdt_days TEXT,                 -- 신용기간
            prdy_vol INTEGER,               -- 전일 거래량
            stck_fcam INTEGER,              -- 주식 액면가
            stck_lstn_date TEXT,            -- 주식 상장 일자
            lstn_stcn INTEGER,              -- 상장 주수
            cpfn INTEGER,                   -- 자본금
            stac_month TEXT,                -- 결산 월
            po_prc INTEGER,                 -- 공모 가격
            prst_cls_code TEXT,             -- 우선주 구분
            sale_account INTEGER,           -- 매출액
            bsop_prfi INTEGER,              -- 영업이익
            op_prfi INTEGER,                -- 경상이익
            thtr_ntin INTEGER,              -- 당기순이익
            roe REAL,                       -- ROE
            base_date TEXT,                 -- 기준년월
            prdy_avls_scal INTEGER,         -- 전일기준 시가총액
            grp_code TEXT,                  -- 그룹사 코드
            co_crdt_limt_over_yn TEXT,      -- 회사신용한도초과
            secu_lend_able_yn TEXT,         -- 담보대출가능
            stln_able_yn TEXT,              -- 대주가능
            
            -- [KOSPI 전용]
            mnin_cls_code_yn TEXT,          -- 제조업 구분
            sprn_strr_nmix_issu_yn TEXT,    -- 지배 구조 지수
            kospi200_apnt_cls_code TEXT,    -- KOSPI200 섹터
            kospi100_issu_yn TEXT,          -- KOSPI100
            kospi50_issu_yn TEXT,           -- KOSPI50
            elw_pblc_yn TEXT,               -- ELW 발행여부
            kospi_issu_yn TEXT,             -- KOSPI 여부
            sri_nmix_yn TEXT,               -- SRI 지수 여부

            -- [KOSDAQ 전용]
            vntr_issu_yn TEXT,              -- 벤처기업 여부
            invt_alrm_yn TEXT,              -- 투자주의환기종목
            ksq150_nmix_yn TEXT,            -- KOSDAQ150 지수
            
            updated_at TEXT,
            
            -- [배당 정보 (추가)]
            per_stock_dvdn_amt INTEGER,     -- 주당 배당금
            dividend_cycle TEXT,            -- 배당 주기
            dividend_count INTEGER          -- 연간 배당 횟수
        )
    """)

    # 2. 일별 시세 및 분석 (핵심 테이블)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_analysis (
            date TEXT,                      -- 날짜 (YYYYMMDD)
            code TEXT,                      -- 종목코드
            
            -- [기본 시세]
            open INTEGER,                   -- 시가
            high INTEGER,                   -- 고가
            low INTEGER,                    -- 저가
            close INTEGER,                  -- 종가
            volume INTEGER,                 -- 거래량
            amount INTEGER,                 -- 거래대금
            market_cap INTEGER,             -- 시가총액
            
            -- [기술적 지표]
            sma_20 REAL,                    -- 20일 이동평균
            sma_50 REAL,                    -- 50일 이동평균
            sma_150 REAL,                   -- 150일 이동평균
            sma_200 REAL,                   -- 200일 이동평균
            volume_sma_50 REAL,             -- 50일 평균 거래량
            high_52w INTEGER,               -- 52주 신고가
            low_52w INTEGER,                -- 52주 신저가
            rs_score REAL,                  -- 상대강도 점수 (0~99)
            vol_std_10d REAL,               -- 10일 변동성 표준편차
            vol_std_50d REAL,               -- 50일 변동성 표준편차
            
            -- [재무/배당 지표]
            dividend_yield REAL,            -- 배당 수익률
            eps REAL,                       -- 주당 순이익
            bps REAL,                       -- 주당 순자산
            revenue_growth REAL,            -- 매출 성장률
            eps_growth REAL,                -- 순이익 성장률
            operating_margin REAL,          -- 영업이익률
            
            -- [수급 데이터 (투자자별 순매수)]
            frgn_net_buy INTEGER,           -- 외국인 순매수
            orgn_net_buy INTEGER,           -- 기관계 순매수
            prsn_net_buy INTEGER,           -- 개인 순매수
            fin_net_buy INTEGER,            -- 금융투자 순매수
            inv_net_buy INTEGER,            -- 투신 순매수
            pension_net_buy INTEGER,        -- 연기금 순매수
            etc_net_buy INTEGER,            -- 기타법인 순매수
            
            PRIMARY KEY (date, code)
        )
    """)

    # 3. 섹터/테마 정보
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sectors_themes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            category_type TEXT,             -- SECTOR / THEME
            category_name TEXT,             -- 분류명 (예: 반도체, 2차전지)
            source TEXT,                    -- 출처 (예: KIS)
            FOREIGN KEY(code) REFERENCES master_info(code)
        )
    """)

    # 4. 뷰 생성 (편의성)
    cur.execute("DROP VIEW IF EXISTS view_trend_candidates")
    cur.execute("""
        CREATE VIEW view_trend_candidates AS
        SELECT 
            d.date, d.code, m.name, m.market_type,
            d.close, d.amount, d.volume, d.volume_sma_50,
            d.sma_50, d.sma_150, d.sma_200, d.rs_score,
            (d.vol_std_10d / d.vol_std_50d) as vcp_ratio,
            d.high_52w
        FROM daily_analysis d
        JOIN master_info m ON d.code = m.code
    """)

    cur.execute("DROP VIEW IF EXISTS view_dividend_candidates")
    cur.execute("""
        CREATE VIEW view_dividend_candidates AS
        SELECT d.code, m.name, d.close, d.dividend_yield,
               COALESCE(m.dividend_cycle, '연배당') as cycle,
               COALESCE(m.per_stock_dvdn_amt, 0) as dps
        FROM daily_analysis d
        JOIN master_info m ON d.code = m.code
        WHERE d.dividend_yield >= 5.0
    """)

    # 5. 매매 계획 테이블 (추가)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS trade_plan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,                      -- 계획 수립일 (YYYY-MM-DD)
            code TEXT,                      -- 종목코드
            name TEXT,                      -- 종목명
            entry_price INTEGER,            -- 진입가
            stop_price INTEGER,             -- 손절가
            weight TEXT,                    -- 비중
            status TEXT DEFAULT 'READY',    -- 상태 (READY, BOUGHT, SOLD, CANCEL)
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("Database schema initialized successfully.")

if __name__ == "__main__":
    init_db()