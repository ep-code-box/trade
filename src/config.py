"""프로젝트 공통 설정: 경로, DB, URL."""
import os

# 프로젝트 루트 (src/config.py 기준 상위)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# DB
STOCK_DB_PATH = os.path.join(ROOT, "TrendHunter", "db", "stock_info.db")

# TrendHunter 하위 디렉터리
TRENDHUNTER_TMP = os.path.join(ROOT, "TrendHunter", "tmp")
TRENDHUNTER_CHARTS = os.path.join(ROOT, "TrendHunter", "charts")
TRENDHUNTER_OUTPUTS = os.path.join(ROOT, "TrendHunter", "outputs")

# DWS 마스터 다운로드 (업종/테마)
DWS_MASTER_BASE_URL = "https://new.real.download.dws.co.kr/common/master/"

# 한국투자증권 API URL은 src.auth에서 로드 (MODE에 따라 real/vts)
