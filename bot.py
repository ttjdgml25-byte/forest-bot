import requests
import os
import json
from datetime import datetime

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
API_KEY = os.environ["DATA_API_KEY"]

BASE = "https://apis.data.go.kr/B551011/KorService2"


def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": message,
        "disable_web_page_preview": True
    })


def main():
    print("=== 관광공사 축제 API 테스트 ===")

    # 축제 조회 - 오늘 이후 시작하는 축제
    today = datetime.now().strftime("%Y%m%d")
    url = f"{BASE}/searchFestival2"
    params = {
        "serviceKey": API_KEY,
        "numOfRows": "3",
        "pageNo": "1",
        "MobileOS": "ETC",
        "MobileApp": "ForestBot",
        "_type": "json",
        "eventStartDate": today,
        "arrange": "A",
    }

    try:
        res = requests.get(url, params=params, timeout=30)
        print(f"상태: {res.status_code}")
        print(f"응답: {res.text[:1500]}")

        try:
            data = res.json()
            items = data.get("response", {}).get("body", {}).get("items", {})
            send_telegram(f"🎪 축제 API 테스트\n상태: {res.status_code}\n\n응답 구조:\n{json.dumps(items, ensure_ascii=False)[:1000]}")
        except Exception:
            send_telegram(f"🎪 축제 API (JSON 파싱실패)\n상태: {res.status_code}\n원본:\n{res.text[:800]}")

    except Exception as e:
        print(f"오류: {e}")
        send_telegram(f"❌ 오류: {str(e)[:200]}")


if __name__ == "__main__":
    main()
