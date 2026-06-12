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

# ✅ 웹페이지 주소 (GitHub Pages - forest-bot)
WEB_URL = "https://ttjdgml25-byte.github.io/forest-bot/"

# 대한민국 구석구석 축제 상세 링크
DETAIL_LINK = "https://korean.visitkorea.or.kr/detail/ms_detail.do?cotId="


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
    if yyyymmdd and len(yyyymmdd) == 8:
        return f"{yyyymmdd[:4]}.{yyyymmdd[4:6]}.{yyyymmdd[6:]}"
    return yyyymmdd


def get_festivals():
    """전국 축제 조회"""
    results = []
    try:
        today = datetime.now().strftime("%Y%m%d")
        url = f"{BASE}/searchFestival2"
        params = {
            "serviceKey": API_KEY,
            "numOfRows": "300",
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

        for item in item_list:
            title = item.get("title", "")
            start = item.get("eventstartdate", "")
            end = item.get("eventenddate", "")
            addr = item.get("addr1", "")
            cid = item.get("contentid", "")
            img = item.get("firstimage", "")
            tel = item.get("tel", "")

            if not title or not start:
                continue

            link = f"{DETAIL_LINK}{cid}" if cid else ""
            results.append({
                "title": title, "start": start, "end": end,
                "addr": addr, "link": link, "img": img, "tel": tel
            })

        results.sort(key=lambda x: x["start"])
        return results
    except Exception as e:
        print(f"축제 조회 오류: {e}")
    return results


def get_forest_schedule():
    today = datetime.now()
    day = today.day
    msg = ""
    if day in [1, 2, 3]:
        msg = "🔔 *국립자연휴양림 예약 신청 임박!*\n  📅 매월 4일 오전 9시: 다음달 추첨 신청 시작\n  💡 숲나들e(foresttrip.go.kr)에서 신청\n"
    elif day == 4:
        msg = "🎯 *오늘! 국립자연휴양림 추첨 신청 시작*\n  ⏰ 오전 9시 ~ 9일까지 신청\n  💡 숲나들e(foresttrip.go.kr)\n"
    elif day in [13, 14]:
        msg = "🔔 *국립자연휴양림 선착순 오픈 임박!*\n  📅 매월 15일 오전 9시: 미당첨분 선착순\n  💡 숲나들e(foresttrip.go.kr)\n"
    elif day == 15:
        msg = "🎯 *오늘! 국립자연휴양림 선착순 오픈*\n  ⏰ 오전 9시 ~ (미당첨분 선착순)\n  💡 숲나들e(foresttrip.go.kr)\n"
    return msg


def main():
    today_str = datetime.now().strftime("%Y년 %m월 %d일 (%A)")
    day_map = {
        "Monday": "월요일", "Tuesday": "화요일", "Wednesday": "수요일",
        "Thursday": "목요일", "Friday": "금요일", "Saturday": "토요일", "Sunday": "일요일"
    }
    for en, ko in day_map.items():
        today_str = today_str.replace(en, ko)

    all_festivals = get_festivals()

    # 60일 이내 시작하는 축제만 텔레그램에
    limit_date = (datetime.now() + timedelta(days=60)).strftime("%Y%m%d")
    soon = [f for f in all_festivals if f["start"] <= limit_date]

    msg = f"🏕 *{today_str} 관광·휴양 브리핑*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n\n"

    forest_msg = get_forest_schedule()
    if forest_msg:
        msg += forest_msg + "━━━━━━━━━━━━━━━━━━━━\n\n"

    if soon:
        msg += f"🎪 *다가오는 축제 ({len(soon)}건)*\n\n"
        for f in soon[:12]:
            msg += f"• *{f['title']}*\n"
            msg += f"  📅 {fmt_date(f['start'])} ~ {fmt_date(f['end'])}\n"
            if f['addr']:
                msg += f"  📍 {f['addr']}\n"
            if f['link']:
                msg += f"  🔗 {f['link']}\n"
            msg += "\n"
        if len(soon) > 12:
            msg += f"...외 {len(soon)-12}건 (웹페이지 참고)\n\n"
    else:
        msg += "🎪 다가오는 축제: 정보 없음\n\n"

    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"📋 *전체 축제 목록 보기*\n{WEB_URL}\n\n"
    msg += "📌 국립휴양림 신청: 매월 4일·15일 오전 9시"

    send_telegram(msg)
    generate_html(all_festivals)
    print(f"✅ 전송 완료 - 전체 {len(all_festivals)}건, 60일내 {len(soon)}건")


def generate_html(festivals):
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>전국 축제 모아보기</title>
<style>
  * {{ box-sizing:border-box; }}
  body {{ font-family:-apple-system,'Malgun Gothic',sans-serif; background:#f5f6fa; margin:0; padding:16px; color:#2c3e50; }}
  h1 {{ text-align:center; font-size:24px; }}
  .update {{ text-align:center; color:#888; font-size:13px; margin-bottom:20px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:16px; }}
  .card {{ background:#fff; border-radius:12px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.08); }}
  .card img {{ width:100%; height:160px; object-fit:cover; }}
  .card-body {{ padding:14px; }}
  .card-title {{ font-weight:bold; font-size:16px; margin-bottom:8px; }}
  .card-date {{ color:#e67e22; font-size:13px; margin-bottom:4px; }}
  .card-addr {{ color:#666; font-size:13px; margin-bottom:10px; }}
  .card-link {{ display:inline-block; background:#3498db; color:#fff; padding:6px 14px; border-radius:6px; font-size:13px; text-decoration:none; }}
  .no-img {{ height:160px; background:linear-gradient(135deg,#74b9ff,#a29bfe); display:flex; align-items:center; justify-content:center; color:#fff; font-size:40px; }}
</style>
</head>
<body>
<h1>🎪 전국 축제 모아보기</h1>
<div class="update">마지막 업데이트: {update_time} | 전체 {len(festivals)}건</div>
<div class="grid">
"""

    for f in festivals:
        html += '<div class="card">\n'
        if f['img']:
            html += f'<img src="{f["img"]}" alt="{f["title"]}" onerror="this.style.display=\'none\'">\n'
        else:
            html += '<div class="no-img">🎪</div>\n'
        html += '<div class="card-body">\n'
        html += f'<div class="card-title">{f["title"]}</div>\n'
        html += f'<div class="card-date">📅 {fmt_date(f["start"])} ~ {fmt_date(f["end"])}</div>\n'
        if f['addr']:
            html += f'<div class="card-addr">📍 {f["addr"]}</div>\n'
        if f['link']:
            html += f'<a class="card-link" href="{f["link"]}" target="_blank">자세히 보기 →</a>\n'
        html += '</div>\n</div>\n'

    html += "</div></body></html>"

    with open("index.html", "w", encoding="utf-8") as fp:
        fp.write(html)
    print("✅ index.html 생성 완료")


if __name__ == "__main__":
    main()
