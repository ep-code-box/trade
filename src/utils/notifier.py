"""텔레그렘 알림 엔진: 실시간 매매 알림 및 리포트 전송."""
import os
import asyncio
from telegram import Bot
from dotenv import load_dotenv
from src.config import ROOT

# 설정 로드
load_dotenv(os.path.join(ROOT, ".env"))

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

class TelegramNotifier:
    def __init__(self):
        self.bot = Bot(token=TOKEN) if TOKEN else None
        self.chat_id = CHAT_ID

    async def send_message_async(self, text: str):
        """비동기 메시지 전송."""
        if not self.bot or not self.chat_id:
            # print("[Telegram] 설정 미비로 메시지를 전송하지 않음.")
            return
        
        try:
            # [v20+] 버전은 비동기 메서드를 사용합니다.
            await self.bot.send_message(chat_id=self.chat_id, text=text, parse_mode="HTML")
        except Exception as e:
            print(f"[Telegram] 전송 실패: {e}")

    def send_message(self, text: str):
        """동기 호출용 래퍼."""
        if not TOKEN or not CHAT_ID: return
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.send_message_async(text))
            else:
                loop.run_until_complete(self.send_message_async(text))
        except:
            # 이벤트 루프가 없는 경우 (새로 생성)
            asyncio.run(self.send_message_async(text))

# 싱글톤 인스턴스
notifier = TelegramNotifier()

if __name__ == "__main__":
    # 테스트 (토큰 설정 후 실행 시 메시지 전송됨)
    test_msg = "🎯 <b>TrendHunter 시스템 가동</b>\n서버가 정상적으로 연결되었습니다."
    notifier.send_message(test_msg)
