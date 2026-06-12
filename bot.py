import requests
from bs4 import BeautifulSoup
import os
import time

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
API_KEY = os.environ["DATA_API_KEY"]

# https와 http 둘 다 시도
URLS = [
    "https://apis.data.go.kr/1400000/nationalRecreationForestReservationService/nationalRecreationForestReservationList",
    "http://apis.data.go.kr/1400000/nationalRecreationForestReservationService/nationalRecreationForestReservationList",
]


def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": message,
        "disable_web_page_preview": True
    })


def main():
    print("=== 휴양림 API 테스트 (재시도) ===")

    params = {
        "serviceKey": API_KEY,
        "pageNo": "1",
        "numOfRows": "1",
    }

    for url in URLS:
        protocol = "HTTPS" if url.startswith("https") else "HTTP"
        # 각 URL당 3번 재시도
        for attempt in range(1, 4):
            try:
                print(f"[{protocol}] 시도 {attempt}...")
                res = requests.get(url, params=params, timeout=30)
                print(f"성공! 상태: {res.status_code}")
                print(f"응답: {res.text[:1200]}")

                soup = BeautifulSoup(res.content, "xml")
                total = soup.find("totalCount")
                result_msg = soup.find("resultMsg") or soup.find("resultMessage")
                total_txt = total.get_text() if total else "?"
                msg_txt = result_msg.get_text() if result_msg else "?"

                first_item = soup.find("item")
                structure = str(first_item)[:800] if first_item else "item없음:\n" + res.text[:500]

                send_telegram(f"🏕 [{protocol}] 성공! (시도 {attempt})\n상태: {res.status_code}\ntotalCount: {total_txt}\nmsg: {msg_txt}\n\n구조:\n{structure}")
                return  # 성공하면 종료

            except Exception as e:
                print(f"[{protocol}] 시도 {attempt} 실패: {str(e)[:80]}")
                time.sleep(3)  # 3초 대기 후 재시도

    # 모든 시도 실패
    send_telegram("❌ HTTPS/HTTP 모두 실패. API 서버가 응답하지 않습니다.")


if __name__ == "__main__":
    main()
