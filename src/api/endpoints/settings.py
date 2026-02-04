from fastapi import APIRouter, HTTPException
import json
import sqlite3
from pydantic import BaseModel
from src.db import get_connection

router = APIRouter(tags=["settings"])

class ConfigUpdate(BaseModel):
    key: str
    value: str

@router.get("/settings")
def get_all_settings():
    """DB에서 모든 시스템 설정을 가져옴"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT key, value FROM system_config")
        rows = cur.fetchall()
        conn.close()
        return {row[0]: row[1] for row in rows}
    except Exception as e:
        return {"error": str(e)}

@router.post("/settings")
def update_setting(config: ConfigUpdate):
    """DB에 설정을 저장하거나 업데이트함"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO system_config (key, value, updated_at)
            VALUES (?, ?, datetime('now', 'localtime'))
        """, (config.key, config.value))
        conn.commit()
        conn.close()
        return {"status": "success", "key": config.key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/settings/batch")
def update_settings_batch(configs: dict):
    """여러 설정을 한 번에 저장"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        for key, value in configs.items():
            # 가독성을 위해 문자열로 변환 (JSON 객체인 경우)
            val_str = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
            cur.execute("""
                INSERT OR REPLACE INTO system_config (key, value, updated_at)
                VALUES (?, ?, datetime('now', 'localtime'))
            """, (key, val_str))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
