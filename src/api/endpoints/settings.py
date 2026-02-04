from fastapi import APIRouter, HTTPException
import json
import sqlite3
from pydantic import BaseModel
from src.db import get_connection

router = APIRouter(tags=["settings"])

class ConfigUpdate(BaseModel):
    key: str
    value: str

import subprocess
import os
import signal

import threading
from run_daily import main as run_daily_main

@router.post("/settings/update-daily")
def trigger_daily_update():
    """통합 데이터 파이프라인(run_daily.py) 즉시 실행"""
    try:
        # 백그라운드 스레드에서 실행 (API 응답 지연 방지)
        thread = threading.Thread(target=run_daily_main)
        thread.start()
        return {"status": "started", "message": "데이터 동기화 파이프라인이 시작되었습니다. (완료 시 텔레그램으로 보고됩니다.)"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/settings/bot/status")
def get_bot_status():
    """텔레그램 봇 리스너 상태 확인"""
    try:
        # 프로세스 이름으로 체크
        res = subprocess.run(["pgrep", "-fl", "bot_listener"], capture_output=True, text=True)
        is_running = "bot_listener" in res.stdout
        return {"status": "running" if is_running else "stopped", "pid": res.stdout.strip()}
    except:
        return {"status": "stopped"}

@router.post("/settings/bot/start")
def start_bot():
    """텔레그램 봇 리스너 시작 (caffeinate 적용)"""
    try:
        # 이미 돌아가는지 확인
        status = get_bot_status()
        if status["status"] == "running":
            return {"status": "already_running"}

        # [v6.6] caffeinate를 사용하여 맥북이 잠들어도 프로세스 유지
        # -i: 시스템 아이들 방지, -s: 시스템 슬립 방지
        cmd = "export PYTHONPATH=$PYTHONPATH:. && nohup caffeinate -is python3 -m src.utils.bot_listener > /tmp/bot_listener.log 2>&1 &"
        subprocess.Popen(cmd, shell=True, executable="/bin/bash")
        return {"status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/settings/bot/stop")
def stop_bot():
    """텔레그램 봇 리스너 종료"""
    try:
        subprocess.run(["pkill", "-9", "-fl", "bot_listener"])
        subprocess.run(["pkill", "-9", "-fl", "caffeinate"])
        return {"status": "stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
