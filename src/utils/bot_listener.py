"""텔레그램 봇 리스너: 사용자의 종목 질의에 실시간 응답 및 명령어 처리."""
import os
import sqlite3
import asyncio
import logging
import subprocess
import sys
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
from dotenv import load_dotenv

from src.auth import get_access_token, load_config_from_db
from src.kis_api import kis_get_raw
from src.config import ROOT

# 설정 로드
load_dotenv(os.path.join(ROOT, ".env"))

# 로그 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

DB_PATH = os.path.join(ROOT, "TrendHunter", "db", "stock_info.db")
TOKEN = os.getenv("TELEGRAM_TOKEN")

def resolve_stock(query: str):
    """이름 또는 코드로 종목 정보를 찾음."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    query = query.strip()
    if query == "엑트로": query = "액트로"
    
    if query.isdigit() and len(query) == 6:
        cur.execute("SELECT code, name FROM master_info WHERE code = ?", (query,))
    else:
        cur.execute("SELECT code, name FROM master_info WHERE name LIKE ?", (f"%{query}%",))
    res = cur.fetchone()
    conn.close()
    return res

def get_shield_info(code: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT stop_price, entry_price, track FROM trade_plan WHERE code = ? ORDER BY id DESC LIMIT 1", (code,))
    res = cur.fetchone()
    conn.close()
    return res

def get_stock_balance_info(code: str):
    try:
        from src.account import get_account_balance
        result = get_account_balance()
        if not result or 'holdings' not in result: return None
        for h in result['holdings']:
            if str(h['code']).strip() == str(code).strip(): return h
        return None
    except: return None

async def post_init(application):
    """봇 시작 시 명령어 메뉴 설정."""
    commands = [
        ("account", "내 계좌 생존 리포트"),
        ("screen", "오늘의 최정예 추천주"),
        ("update", "데이터 전체 갱신 실행"),
        ("log", "시스템 로그 확인"),
        ("help", "사용법 안내")
    ]
    await application.bot.set_my_commands(commands)

async def cmd_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/log: 파이프라인 최신 로그 15줄 전송."""
    log_path = "/tmp/pipeline.log"
    try:
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                lines = f.readlines()
                last_logs = "".join(lines[-15:])
                await update.message.reply_html(f"<b>📄 파이프라인 로그 (최근 15줄)</b>\n<pre>{last_logs}</pre>")
        else:
            await update.message.reply_text("파이프라인 로그 파일을 찾을 수 없습니다. 아직 실행 전이거나 경로를 확인하세요.")
    except Exception as e:
        await update.message.reply_text(f"로그 조회 실패: {e}")

async def cmd_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/update: 데이터 파이프라인 즉시 실행 (정석 구현)."""
    logger.info(">>> /update 명령어 수신됨")
    
    await update.message.reply_text("🔄 <b>데이터 동기화 및 RS 분석을 시작합니다.</b>\n(완료 시 리포트가 자동 전송됩니다.)", parse_mode="HTML")
    
    # 실행 환경 구축
    script_path = os.path.join(ROOT, "run_daily.py")
    log_file = open("/tmp/pipeline.log", "a")
    
    # PYTHONPATH 강제 주입: ROOT를 맨 앞에 배치
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{ROOT}:{env.get('PYTHONPATH', '')}"
    
    # subprocess 실행 흐름: 
    # 1. sys.executable을 사용하여 현재 파이썬 인터프리터 유지
    # 2. stdout/stderr를 별도 파일로 리다이렉트하여 로그 격리
    # 3. start_new_session=True로 부모 프로세스와의 생명주기 분리 (완전 독립)
    try:
        subprocess.Popen(
            [sys.executable, "-u", script_path],
            env=env,
            cwd=ROOT,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True
        )
        logger.info(f"파이프라인 독립 프로세스 가동 성공 (CWD: {ROOT})")
    except Exception as e:
        logger.error(f"파이프라인 가동 실패: {str(e)}")
        await update.message.reply_text(f"❌ 가동 실패: {str(e)}")

async def cmd_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from src.account import print_account_info
    print_account_info()
    await update.message.reply_text("📋 계좌 생존 리포트를 전송했습니다.")

async def cmd_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from src.analysis.screen_market import generate_full_report
    generate_full_report()
    await update.message.reply_text("🚀 최신 스크린 리포트를 분석하여 전송했습니다.")

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = "<b>🤖 TrendHunter 봇 사용법</b>\n\n"
    help_text += "1. <b>종목 질의</b>: 종목명(예: 액트로)이나 티커(290740)를 입력하면 실시간 시세와 이익 쿠션을 분석합니다.\n"
    help_text += "2. <b>/account</b>: 현재 내 계좌의 생존 상태를 확인합니다.\n"
    help_text += "3. <b>/screen</b>: 시장 주도주와 배당 마법공식 추천주를 즉시 분석합니다.\n"
    help_text += "4. <b>/update</b>: 전체 데이터 동기화 파이프라인을 실행합니다.\n"
    help_text += "5. <b>/log</b>: 현재 실행 중인 파이프라인의 로그를 확인합니다.\n"
    await update.message.reply_html(help_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    query = update.message.text.strip()
    if query.startswith('/'): return

    stock = resolve_stock(query)
    if not stock:
        await update.message.reply_text(f"❓ '{query}' 종목을 찾을 수 없습니다.")
        return

    code, name = stock
    path = "/uapi/domestic-stock/v1/quotations/inquire-price"
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code}
    res = kis_get_raw(path, params=params, tr_id="FHKST01010100")
    if not res or 'output' not in res:
        await update.message.reply_text(f"❌ [{name}] 시세 조회 실패")
        return

    curr_price = int(res['output']['stck_prpr'])
    change_pct = res['output']['prdy_ctrt']
    pos = get_stock_balance_info(code)
    
    from src.auth import MODE
    mode_str = "실전" if MODE == "real" else "모의"
    msg = f"📊 <b>{name} ({code}) {mode_str} 점검</b>\n"
    msg += f"────────────────\n"
    msg += f"• 현재가: <b>{curr_price:,}원</b> ({change_pct}%)\n"
    
    if pos:
        msg += f"• <b>나의 평단가: {int(pos['buy_price']):,}원</b>\n"
        if pos['stop_price'] > 0:
            cushion = int(curr_price - pos['stop_price'])
            cushion_pct = (cushion / pos['stop_price'] * 100) if pos['stop_price'] > 0 else 0
            msg += f"• Shield: {int(pos['stop_price']):,}\n"
            msg += f"• <b>이익 쿠션: +{cushion:,}원 (+{cushion_pct:.1f}%)</b>\n"
        msg += f"• <b>현재 수익: {int((curr_price - pos['buy_price']) * pos['qty']):,}원</b>\n"
    else:
        shield_data = get_shield_info(code)
        if shield_data:
            msg += f"• <i>(미보유 종목)</i>\n"
            msg += f"• 목표 진입가: {shield_data[1]:,}원\n"
            msg += f"• 예상 Shield: {shield_data[0]:,}원\n"

    msg += f"────────────────\n"
    msg += f"💡 <i>복사용 티커: <code>{code}</code></i>"
    await update.message.reply_html(msg)

if __name__ == "__main__":
    if not TOKEN:
        print("TELEGRAM_TOKEN이 설정되지 않았습니다.")
    else:
        application = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
        application.add_handler(CommandHandler("account", cmd_account))
        application.add_handler(CommandHandler("screen", cmd_screen))
        application.add_handler(CommandHandler("update", cmd_update))
        application.add_handler(CommandHandler("log", cmd_log))
        application.add_handler(CommandHandler("help", cmd_help))
        application.add_handler(CommandHandler("start", cmd_help))
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        application.run_polling()