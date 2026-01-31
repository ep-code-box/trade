"""DWS 업종/테마 ZIP 다운로드 후 sectors_themes 적재. 실행: python -m src.jobs.db_sync_themes"""
import os
import ssl
import urllib.request
import zipfile

from src.config import TRENDHUNTER_TMP, DWS_MASTER_BASE_URL
from src.db import get_connection


def download_and_extract(file_name_zip, extracted_file_name):
    url = DWS_MASTER_BASE_URL + file_name_zip
    local_zip_path = os.path.join(TRENDHUNTER_TMP, file_name_zip)
    local_file_path = os.path.join(TRENDHUNTER_TMP, extracted_file_name)

    os.makedirs(TRENDHUNTER_TMP, exist_ok=True)
    print(f"Downloading {file_name_zip}...")
    ssl._create_default_https_context = ssl._create_unverified_context
    urllib.request.urlretrieve(url, local_zip_path)
    with zipfile.ZipFile(local_zip_path, "r") as z:
        z.extractall(TRENDHUNTER_TMP)
    print(f"Extracted to {local_file_path}")
    return local_file_path


def sync_sectors(file_path):
    if not os.path.exists(file_path):
        return
    conn = get_connection()
    cur = conn.cursor()
    count = 0
    print("Parsing and syncing sectors...")
    with open(file_path, mode="r", encoding="cp949") as f:
        for row in f:
            try:
                tcode = row[1:5].strip()
                tname = row[3:43].strip()
                if tcode and tname:
                    cur.execute(
                        "INSERT INTO sectors_themes (code, category_type, category_name, source) VALUES (?, 'SECTOR_MASTER', ?, 'KIS')",
                        (tcode, tname),
                    )
                    count += 1
            except Exception:
                continue
    conn.commit()
    conn.close()
    print(f"Synced {count} sectors.")


def sync_themes(file_path):
    if not os.path.exists(file_path):
        return
    conn = get_connection()
    cur = conn.cursor()
    count = 0
    print("Parsing and syncing themes...")
    with open(file_path, mode="r", encoding="cp949") as f:
        for row in f:
            try:
                tcode = row[0:3].strip()
                jcode_raw = row[-10:].strip()
                tname = row[3:-10].strip()
                jcode = jcode_raw[1:] if jcode_raw.startswith("A") else jcode_raw
                if tcode and tname and jcode:
                    cur.execute(
                        "INSERT INTO sectors_themes (code, category_type, category_name, source) VALUES (?, 'THEME', ?, 'KIS')",
                        (jcode, tname),
                    )
                    count += 1
            except Exception:
                continue
    conn.commit()
    conn.close()
    print(f"Synced {count} theme mappings.")


if __name__ == "__main__":
    sector_file = download_and_extract("idxcode.mst.zip", "idxcode.mst")
    sync_sectors(sector_file)
    theme_file = download_and_extract("theme_code.mst.zip", "theme_code.mst")
    sync_themes(theme_file)
