"""텔레그렘 알림 엔진: 실시간 매매 알림 및 리포트 전송."""
import os
import requests
import threading
from dotenv import load_dotenv
from src.config import ROOT

# 설정 로드
load_dotenv(os.path.join(ROOT, ".env"))

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

class TelegramNotifier:
    def __init__(self):
        self.token = TOKEN
        self.chat_id = CHAT_ID

    def _send_actual(self, text: str):
        """실제 HTTP 요청을 수행하는 내부 함수."""
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": text, "parse_mode": "HTML"}
        try:
            resp = requests.post(url, json=payload, timeout=10)
            if not resp.ok:
                print(f"[Telegram] 전송 실패: {resp.text}")
        except Exception as e:
            print(f"[Telegram] 네트워크 오류: {e}")

    def send_message(self, text: str, sync: bool = False):
        """메시지를 전송합니다. sync=True인 경우 전송 완료까지 대기합니다."""
        if not self.token or not self.chat_id:
            print("[Telegram] 토큰 혹은 채팅 ID가 설정되지 않았습니다.")
            return
        
        if sync:
            self._send_actual(text)
        else:
            # 별도의 스레드를 생성하여 즉시 실행 (메인 흐름 방해 금지)
            thread = threading.Thread(target=self._send_actual, args=(text,))
            thread.daemon = True 
            thread.start()

# 싱글톤 인스턴스
notifier = TelegramNotifier()

if __name__ == "__main__":
    # 테스트 (토큰 설정 후 실행 시 메시지 전송됨)
    test_msg = "🎯 <b>TrendHunter 시스템 가동</b>\n서버가 정상적으로 연결되었습니다."
    notifier.send_message(test_msg)
