import os
import sys
from datetime import date, datetime

import requests
import vnlunar

DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL")
BIRTH_DATE_1 = os.environ.get("BIRTH_DATE_1")
BIRTH_DATE_2 = os.environ.get("BIRTH_DATE_2")

COLOR_GREEN = 0x00AA55
COLOR_RED = 0xCC4444
COLOR_GOLD = 0xD4A017
COLOR_BLUE = 0x446688

CAN = [
    "Giáp", "Ất", "Bính", "Đinh", "Mậu",
    "Kỷ", "Canh", "Tân", "Nhâm", "Quý",
]
CHI = [
    "Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ",
    "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi",
]
HOURS = [
    ("Tý", "23:00–1:00"), ("Sửu", "1:00–3:00"),
    ("Dần", "3:00–5:00"), ("Mão", "5:00–7:00"),
    ("Thìn", "7:00–9:00"), ("Tỵ", "9:00–11:00"),
    ("Ngọ", "11:00–13:00"), ("Mùi", "13:00–15:00"),
    ("Thân", "15:00–17:00"), ("Dậu", "17:00–19:00"),
    ("Tuất", "19:00–21:00"), ("Hợi", "21:00–23:00"),
]

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

    fields.append({
        "name": "🌟 Tinh tú",
        "value": f"Sao: **{r['12_star']}**  ({r.get('12_star_desc', '')})",
        "inline": False,
    })

    hours_val = r.get("auspicious_hours", "")
    if hours_val:
        formatted = ", ".join(hours_val.split(", "))
        fields.append({"name": "🕐 Hoàng Đạo (giờ tốt)", "value": formatted, "inline": False})

    conf = r.get("conflict", "")
    if conf:
        fields.append({
            "name": "⚡ Xung khắc",
            "value": conf,
            "inline": False,
        })

    embed = {
        "title": f"{r['status_icon']} LỊCH ÂM — {r['solar']} ({r['dow']})",
        "description": (
            f"**{r['status_text']}** · {r.get('28_mansion_desc', '')}"
        ),
        "color": COLOR_GREEN if r["status_icon"] == "🟢" else COLOR_RED,
        "fields": fields,
        "footer": {"text": "Lịch Âm Bot • " + datetime.now().strftime("%H:%M %d/%m/%Y")},
    }
    return embed


def parse_birth_date(spec: str):
    parts = spec.strip().split()
    date_part = parts[0]
    hour_part = parts[1] if len(parts) > 1 else "0"
    d, m, y = map(int, date_part.split("/"))

    hour_chi = 0
    h = int(hour_part) if hour_part.isdigit() else 0
    if h == 0 or h == 23:
        hour_chi = 0
    elif h <= 2:
        hour_chi = 1
    elif h <= 4:
        hour_chi = 2
    elif h <= 6:
        hour_chi = 3
    elif h <= 8:
        hour_chi = 4
    elif h <= 10:
        hour_chi = 5
    elif h <= 12:
        hour_chi = 6
    elif h <= 14:
        hour_chi = 7
    elif h <= 16:
        hour_chi = 8
    elif h <= 18:
        hour_chi = 9
    elif h <= 20:
        hour_chi = 10
    else:
        hour_chi = 11

    try:
        lunar = vnlunar.get_lunar_date(d, m, y)
        cc = vnlunar.get_can_chi(lunar)
        nayin = vnlunar.get_nayin(lunar["year"])
    except Exception:
        lunar = {"day": d, "month": m, "year": y}
        cc = {"day": "", "month": "", "year": ""}
        nayin = {"name": "", "element": ""}

    ly = lunar["year"]
    return {
        "solar": f"{d:02d}/{m:02d}/{y}",
        "lunar": f"{lunar['day']}/{lunar['month']}/{lunar['year']}",
        "hour": HOURS[hour_chi][0],
        "hour_range": HOURS[hour_chi][1],
        "can_chi_year": cc.get("year", ""),
        "can_chi_day": cc.get("day", ""),
        "can_chi_month": cc.get("month", ""),
        "nap_am": nayin.get("name", ""),
        "menh": nayin.get("element", ""),
    }


def build_birth_embed(birth: dict, label: str):
    fields = [
        {"name": "📅 Dương lịch", "value": birth["solar"], "inline": True},
        {"name": "🌙 Âm lịch", "value": birth["lunar"], "inline": True},
        {"name": "🕐 Giờ sinh", "value": f"**{birth['hour']}** ({birth['hour_range']})", "inline": False},
        {"name": "☯ Trụ năm", "value": birth["can_chi_year"], "inline": True},
        {"name": "☯ Trụ tháng", "value": birth.get("can_chi_month", ""), "inline": True},
        {"name": "☯ Trụ ngày", "value": birth["can_chi_day"], "inline": True},
        {"name": "🔮 Nạp Âm", "value": birth["nap_am"], "inline": True},
        {"name": "🔥 Mệnh", "value": f"**{birth['menh']}**", "inline": True},
    ]

    return {
        "title": f"📜 {label}",
        "color": COLOR_GOLD,
        "fields": fields,
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

    if BIRTH_DATE_1:
        try:
            print(f"  Parsing birth date 1: {BIRTH_DATE_1}")
            b1 = parse_birth_date(BIRTH_DATE_1)
            embeds.append(build_birth_embed(b1, "LÁ SỐ #1 — Nam 01/01/1997"))
        except Exception as e:
            print(f"  Error birth 1: {e}")

    if BIRTH_DATE_2:
        try:
            print(f"  Parsing birth date 2: {BIRTH_DATE_2}")
            b2 = parse_birth_date(BIRTH_DATE_2)
            embeds.append(build_birth_embed(b2, "LÁ SỐ #2 — Nam 28/03/1996"))
        except Exception as e:
            print(f"  Error birth 2: {e}")

    send_discord(embeds)
    print(f"Sent {len(embeds)} embed(s) to Discord ✓")


if __name__ == "__main__":
    main()
