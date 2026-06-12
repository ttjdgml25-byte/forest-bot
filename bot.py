import requests
import os
from datetime import datetime, timedelta

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_IDS = [
    os.environ["CHAT_ID"],
    os.environ.get("CHAT_ID_2", ""),
]
CHAT_IDS = [c for c in CHAT_IDS if c]
API_KEY = os.environ["DATA_API_KEY"]

BASE = "https://apis.data.go.kr/B551011/KorService2"


def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    max_len = 4000
    chunks = [message[i:i+max_len] for i in range(0, len(message), max_len)]
    for chat_id in CHAT_IDS:
        for chunk in chunks:
            requests.post(url, data={
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            })


def fmt_date(yyyymmdd):
    """20261016 → 2026.10.16"""
    if yyyymmdd and len(yyyymmdd) == 8:
        return f"{yyyymmdd[:4]}.{yyyymmdd[4:6]}.{yyyymmdd[6:]}"
    return yyyymmdd


def get_festivals():
    """이번달~다음달 시작 축제 조회"""
    results = []
    try:
        today = datetime.now().strftime("%Y%m%d")
        url = f"{BASE}/searchFestival2"
        params = {
            "serviceKey": API_KEY,
            "numOfRows": "100",
            "pageNo": "1",
            "MobileOS": "ETC",
            "MobileApp": "ForestBot",
            "_type": "json",
            "eventStartDate": today,
            "arrange": "A",
        }
        res = requests.get(url, params=params, timeout=30)
        data = res.json()
        items = data.get("response", {}).get("body", {}).get("items", {})
        if not items:
            return results
        item_list = items.get("item", [])
        if isinstance(item_list, dict):
            item_list = [item_list]

        # 다음 60일 이내 시작하는 축제만
        limit_date = (datetime.now() + timedelta(days=60)).strftime("%Y%m%d")

        for item in item_list:
            title = item.get("title", "")
            start = item.get("eventstartdate", "")
            end = item.get("eventenddate", "")
            addr = item.get("addr1", "")

            if not title or not start:
                continue
            if start > limit_date:  # 60일 이후는 제외
                continue

            entry = f"• *{title}*\n  📅 {fmt_date(start)} ~ {fmt_date(end)}"
            if addr:
                entry += f"\n  📍 {addr}"
            results.append((start, entry))

        # 시작일 순 정렬
        results.sort(key=lambda x: x[0])
        return [e for _, e in results]

    except Exception as e:
        print(f"축제 조회 오류: {e}")
    return results


def get_forest_schedule():
    """국립자연휴양림 매월 신청일 안내 (고정 일정)"""
    today = datetime.now()
    day = today.day

    msg = ""
    # 신청일 임박 알림
    if day in [1, 2, 3]:
        msg = "🔔 *국립자연휴양림 예약 신청 임박!*\n"
        msg += "  📅 매월 4일 오전 9시: 다음달 추첨 신청 시작\n"
        msg += "  💡 숲나들e(foresttrip.go.kr)에서 신청\n"
    elif day == 4:
        msg = "🎯 *오늘! 국립자연휴양림 추첨 신청 시작*\n"
        msg += "  ⏰ 오전 9시 ~ 9일까지 신청\n"
        msg += "  💡 숲나들e(foresttrip.go.kr)\n"
    elif day in [13, 14]:
        msg = "🔔 *국립자연휴양림 선착순 오픈 임박!*\n"
        msg += "  📅 매월 15일 오전 9시: 미당첨분 선착순\n"
        msg += "  💡 숲나들e(foresttrip.go.kr)\n"
    elif day == 15:
        msg = "🎯 *오늘! 국립자연휴양림 선착순 오픈*\n"
        msg += "  ⏰ 오전 9시 ~ (미당첨분 선착순)\n"
        msg += "  💡 숲나들e(foresttrip.go.kr)\n"

    return msg


def main():
    today_str = datetime.now().strftime("%Y년 %m월 %d일 (%A)")
    day_map = {
        "Monday": "월요일", "Tuesday": "화요일", "Wednesday": "수요일",
        "Thursday": "목요일", "Friday": "금요일", "Saturday": "토요일", "Sunday": "일요일"
    }
    for en, ko in day_map.items():
        today_str = today_str.replace(en, ko)

    msg = f"🏕 *{today_str} 관광·휴양 브리핑*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n\n"

    # 1. 휴양림 신청일 알림 (해당일에만)
    forest_msg = get_forest_schedule()
    if forest_msg:
        msg += forest_msg + "\n"
        msg += "━━━━━━━━━━━━━━━━━━━━\n\n"

    # 2. 다가오는 축제 (60일 이내)
    festivals = get_festivals()
    if festivals:
        msg += f"🎪 *다가오는 축제 ({len(festivals)}건)*\n\n"
        msg += "\n\n".join(festivals[:15]) + "\n\n"
        if len(festivals) > 15:
            msg += f"...외 {len(festivals)-15}건 더\n\n"
    else:
        msg += "🎪 다가오는 축제: 정보 없음\n\n"

    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += "📌 국립휴양림 신청: 매월 4일·15일 오전 9시"

    send_telegram(msg)
    print(f"✅ 전송 완료 - 축제 {len(festivals)}건")


if __name__ == "__main__":
    main()
