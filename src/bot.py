import os
import re
import sys
from datetime import date, datetime

import requests
import vnlunar

DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL")

COLOR_GREEN = 0x00AA55
COLOR_RED = 0xCC4444
COLOR_GOLD = 0xD4AF37
COLOR_BLUE = 0x3399FF


def get_daily_report():
    today = date.today()
    info = vnlunar.get_full_info(today.day, today.month, today.year)
    lunar = info["lunar"]
    cc = info["can_chi"]
    el = info["elements"]
    st12 = info.get("12_stars", {})
    con12 = info.get("12_constructions", {})
    gods12 = info.get("12_gods", {})
    mans28 = info.get("28_mansions", {})
    day_type = info.get("day_type", {})
    nayin = info.get("nayin", {})
    hours = info.get("auspicious_hours", "")
    directions = info.get("directions", {})
    conflicting = info.get("conflicting_ages", {})

    is_hoangdao = day_type.get("good", True)
    status_icon = "🟢" if is_hoangdao else "🔴"
    status_text = day_type.get("type", "Hoàng Đạo")

    return {
        "solar": f"{today.day:02d}/{today.month:02d}/{today.year}",
        "dow": info.get("day_of_week", ""),
        "lunar": f"{lunar['day']}/{lunar['month']}/{lunar['year']}",
        "leap": lunar["leap"],
        "month_name": lunar.get("month_name", f"Tháng {lunar['month']}"),
        "can_chi_day": cc.get("day", ""),
        "can_chi_month": cc.get("month", ""),
        "can_chi_year": cc.get("year", ""),
        "animal": el.get("year", {}).get("animal", ""),
        "day_element": el.get("day", {}),
        "nayin": nayin.get("name", ""),
        "status_icon": status_icon,
        "status_text": status_text,
        "12_star": st12.get("name", ""),
        "12_star_status": st12.get("status", ""),
        "12_star_desc": st12.get("description", ""),
        "construction": con12.get("name", ""),
        "construction_good": con12.get("good_for", []),
        "construction_bad": con12.get("bad_for", []),
        "god": gods12.get("name", ""),
        "god_type": gods12.get("type", ""),
        "28_mansion": mans28.get("name", ""),
        "28_mansion_good": mans28.get("good", False),
        "28_mansion_desc": mans28.get("description", ""),
        "auspicious_hours": hours,
        "good_directions": directions.get("good_text", ""),
        "bad_directions": directions.get("bad_text", ""),
        "conflict": conflicting.get("description", ""),
    }


def build_daily_embed(r):
    fields = [
        {
            "name": "🌙 Âm lịch",
            "value": (
                f"**{r['lunar']}** ({r['month_name']})\n"
                f"Năm **{r['can_chi_year']}** – Tuổi **{r['animal']}**"
            ),
            "inline": False,
        },
        {
            "name": "☯ Can Chi",
            "value": f"Ngày **{r['can_chi_day']}** · Tháng **{r['can_chi_month']}**\nNạp Âm: **{r['nayin']}**",
            "inline": False,
        },
    ]

    star_line = f"⭐ **{r['28_mansion']}** ({r.get('28_mansion_desc', '')})"
    if r["28_mansion_good"]:
        star_line = f"🟢 {star_line}"
    else:
        star_line = f"🔴 {star_line}"
    fields.append({"name": "Nhị Thập Bát Tú", "value": star_line, "inline": True})

    truc_line = f"🛠️ **{r['construction']}**"
    if r["construction_good"]:
        truc_line += f"\n✅ Nên: {', '.join(r['construction_good'])}"
    if r["construction_bad"]:
        truc_line += f"\n❌ Kiêng: {', '.join(r['construction_bad'])}"
    fields.append({"name": "Kiến Trừ", "value": truc_line, "inline": True})

    fields.append(
        {
            "name": "🌟 Tinh tú",
            "value": f"Sao: **{r['12_star']}**  ({r.get('12_star_desc', '')})",
            "inline": False,
        }
    )

    hours_val = r.get("auspicious_hours", "")
    if hours_val:
        formatted = ", ".join(hours_val.split(", "))
        fields.append(
            {"name": "🕐 Hoàng Đạo (giờ tốt)", "value": formatted, "inline": False}
        )

    conf = r.get("conflict", "")
    if conf:
        fields.append(
            {
                "name": "⚡ Xung khắc",
                "value": conf,
                "inline": False,
            }
        )

    embed = {
        "title": f"{r['status_icon']} LỊCH ÂM — {r['solar']} ({r['dow']})",
        "description": (f"**{r['status_text']}** · {r.get('28_mansion_desc', '')}"),
        "color": COLOR_GREEN if r["status_icon"] == "🟢" else COLOR_RED,
        "fields": fields,
        "footer": {
            "text": "Lịch Âm Bot • " + datetime.now().strftime("%H:%M %d/%m/%Y")
        },
    }
    return embed


GOLD_BTMC = (
    "http://api.btmc.vn/api/BTMCAPI/getpricebtmc?key=3kd8ub1llcg9t45hnoh8hmn7t5kc2v"
)
UA = {"User-Agent": "Mozilla/5.0 (lunar-calendar-bot)"}


def get_gold_price():
    """Trả (list, nguồn). Nguồn chính: BTMC API (JSON ổn định); dự phòng: scrape webgia."""
    # 1) BTMC API
    try:
        d = requests.get(GOLD_BTMC, headers=UA, timeout=15).json()
        rows = d.get("DataList", {}).get("Data", [])
        out = []
        for r in rows:
            i = r.get("@row")
            name = (r.get(f"@n_{i}") or "").strip()
            try:
                buy, sell = int(r.get(f"@pb_{i}", 0)), int(r.get(f"@ps_{i}", 0))
            except (TypeError, ValueError):
                continue
            if sell > 0 and name:
                out.append({"name": name, "buy": buy, "sell": sell})
        if out:
            return out[:5], "BTMC"
    except Exception as e:
        print(f"BTMC gold error: {e}")
    # 2) Dự phòng: scrape webgia.com (kèm User-Agent)
    try:
        r = requests.get("https://webgia.com/gia-vang/", headers=UA, timeout=15)
        r.raise_for_status()
        gold_list = []
        for m in re.finditer(
            r"<td><a[^>]*><strong>(SJC|PNJ|DOJI)</strong></a></td>\s*"
            r"<td[^>]*>([\d.]+)</td>\s*"
            r"<td[^>]*>([\d.]+)</td>",
            r.text,
        ):
            buy = int(m.group(2).replace(".", ""))
            sell = int(m.group(3).replace(".", ""))
            gold_list.append({"name": m.group(1), "buy": buy, "sell": sell})
        if gold_list:
            return gold_list, "webgia.com"
        print("No gold prices found in webgia.com")
    except Exception as e:
        print(f"webgia gold error: {e}")
    return None, None


def get_hcm_weather():
    try:
        r = requests.get("https://wttr.in/Ho+Chi+Minh?format=j1", timeout=15)
        r.raise_for_status()
        d = r.json()
        cc = d["current_condition"][0]
        astro = d["weather"][0]["astronomy"][0]
        forecast = d["weather"][1] if len(d["weather"]) > 1 else d["weather"][0]
        return {
            "temp": cc["temp_C"],
            "feels": cc["FeelsLikeC"],
            "humidity": cc["humidity"],
            "wind": cc["windspeedKmph"],
            "condition": cc["weatherDesc"][0]["value"],
            "uv": cc["uvIndex"],
            "sunrise": astro["sunrise"],
            "sunset": astro["sunset"],
            "tomorrow": forecast.get("date", ""),
            "tomorrow_temp_max": forecast.get("maxtempC", ""),
            "tomorrow_temp_min": forecast.get("mintempC", ""),
        }
    except Exception as e:
        print(f"Weather API error: {e}")
        return None


def build_gold_embed(gold_list, source="BTMC"):
    lines = []
    for g in gold_list:
        name = g["name"] if len(g["name"]) <= 40 else g["name"][:39] + "…"
        lines.append(f"**{name}**\nMua **{g['buy']:,}**₫ — Bán **{g['sell']:,}**₫")
    fields = [
        {
            "name": "🏦 Giá vàng trong nước (₫)",
            "value": "\n".join(lines),
            "inline": False,
        },
    ]
    return {
        "title": "💰 GIÁ VÀNG HÔM NAY",
        "color": COLOR_GOLD,
        "fields": fields,
        "footer": {"text": f"{source} • " + datetime.now().strftime("%H:%M %d/%m/%Y")},
    }


def build_weather_embed(w):
    fields = [
        {
            "name": "🌡️ Nhiệt độ",
            "value": f"**{w['temp']}°C** (cảm giác {w['feels']}°C)",
            "inline": True,
        },
        {"name": "💧 Độ ẩm", "value": f"**{w['humidity']}%**", "inline": True},
        {"name": "🌬️ Gió", "value": f"**{w['wind']}** km/h", "inline": True},
        {"name": "☀️ UV", "value": f"Chỉ số: **{w['uv']}**", "inline": True},
        {
            "name": "🌅 Mặt trời",
            "value": f"Mọc **{w['sunrise']}** • Lặn **{w['sunset']}**",
            "inline": True,
        },
        {"name": "\u200b", "value": "\u200b", "inline": True},
        {
            "name": "📅 Ngày mai",
            "value": (
                f"Cao nhất **{w['tomorrow_temp_max']}°C** – "
                f"Thấp nhất **{w['tomorrow_temp_min']}°C**"
            ),
            "inline": False,
        },
    ]
    return {
        "title": f"🌤️ THỜI TIẾT TP. HCM — {w['condition']}",
        "color": COLOR_BLUE,
        "fields": fields,
        "footer": {"text": "wttr.in • " + datetime.now().strftime("%H:%M %d/%m/%Y")},
    }


def send_discord(embeds: list):
    if not DISCORD_WEBHOOK:
        print("FATAL: DISCORD_WEBHOOK_URL not set")
        sys.exit(1)

    for i in range(0, len(embeds), 10):
        batch = embeds[i : i + 10]
        r = requests.post(DISCORD_WEBHOOK, json={"embeds": batch})
        r.raise_for_status()


def main():
    print("Building daily lunar calendar...")
    report = get_daily_report()
    daily_embed = build_daily_embed(report)

    embeds = [daily_embed]

    gold, gold_src = get_gold_price()
    if gold:
        embeds.append(build_gold_embed(gold, gold_src))
    else:
        embeds.append(
            {
                "title": "💰 GIÁ VÀNG HÔM NAY",
                "color": COLOR_GOLD,
                "description": "_Chưa lấy được giá vàng hôm nay (nguồn lỗi)._",
                "footer": {
                    "text": "lunar-bot • " + datetime.now().strftime("%H:%M %d/%m/%Y")
                },
            }
        )
        print("Gold unavailable → hiện thông báo thay vì bỏ qua")

    weather = get_hcm_weather()
    if weather:
        embeds.append(build_weather_embed(weather))
    else:
        print("Skipping weather (unavailable)")

    send_discord(embeds)
    print(f"Sent {len(embeds)} embed(s) to Discord ✓")


if __name__ == "__main__":
    main()
