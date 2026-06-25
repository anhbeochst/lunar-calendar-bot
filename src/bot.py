import os
import sys
from datetime import date, datetime

import requests
import vnlunar

DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL")

COLOR_GREEN = 0x00AA55
COLOR_RED = 0xCC4444

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
    send_discord([daily_embed])
    print("Sent daily report to Discord ✓")


if __name__ == "__main__":
    main()
