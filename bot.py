import requests
from bs4 import BeautifulSoup
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
API_KEY = os.environ["DATA_API_KEY"]

URL = "https://apis.data.go.kr/1400000/nationalRecreationForestReservationService/nationalRecreationForestReservationList"


def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": message,
        "disable_web_page_preview": True
    })


def main():
    print("=== 휴양림 API 테스트 ===")

    # numOfRows를 1로 최소화, 타임아웃 60초로 증가
    params = {
        "serviceKey": API_KEY,
        "pageNo": "1",
        "numOfRows": "1",
    }

    try:
        res = requests.get(URL, params=params, timeout=60)
        print(f"상태: {res.status_code}")
        print(f"응답: {res.text[:1500]}")

        soup = BeautifulSoup(res.content, "xml")
        total = soup.find("totalCount")
        result_msg = soup.find("resultMsg") or soup.find("resultMessage")
        total_txt = total.get_text() if total else "?"
        msg_txt = result_msg.get_text() if result_msg else "?"

        first_item = soup.find("item")
        item_structure = str(first_item)[:900] if first_item else "item 없음. 전체응답:\n" + res.text[:600]

        tg_msg = f"🏕 휴양림 API 테스트\n상태: {res.status_code}\ntotalCount: {total_txt}\nmsg: {msg_txt}\n\n구조:\n{item_structure}"
        send_telegram(tg_msg)

    except Exception as e:
        print(f"오류: {e}")
        send_telegram(f"❌ 오류: {str(e)[:200]}")


if __name__ == "__main__":
    main()
