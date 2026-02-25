import os
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

# ── Configuration ─────────────────────────────────────────────────────────────
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
TIMEZONE = os.environ.get("TIMEZONE", "Australia/Melbourne")

MELBOURNE = ZoneInfo(TIMEZONE)

# ── Category display order and labels ─────────────────────────────────────────
CATEGORY_ORDER = [
    ("Respond",    "🔴 Respond"),
    ("Waiting",    "🟡 Waiting"),
    ("Compliance", "🟣 Compliance"),
    ("Strategic",  "🔵 Strategic"),
    ("Reference",  "⚪ Reference"),
]

# ── Supabase REST query ───────────────────────────────────────────────────────
def fetch_open_items():
    url = f"{SUPABASE_URL}/rest/v1/brain_items"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    params = {
        "status": "eq.open",
        "order": "category.asc,due_date.asc.nullslast,event_timestamp.asc",
        "select": "*",
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

# ── Group items by category ───────────────────────────────────────────────────
def group_by_category(items):
    grouped = {cat: [] for cat, _ in CATEGORY_ORDER}
    for item in items:
        cat = item.get("category")
        if cat in grouped:
            grouped[cat].append(item)
    return grouped

# ── Format a single item line ─────────────────────────────────────────────────
def format_item(item):
    description = item.get("description", "").strip()
    stakeholder = item.get("stakeholder")
    due_date = item.get("due_date")

    line = f"- {description}"
    if stakeholder:
        line += f" ({stakeholder})"
    if due_date:
        try:
            d = datetime.strptime(due_date, "%Y-%m-%d")
            line += f" — due {d.strftime('%d %b')}"
        except ValueError:
            line += f" — due {due_date}"
    return line

# ── Build the full message ────────────────────────────────────────────────────
def build_message(grouped, total):
    lines = ["Good morning ☀️", ""]

    for cat_key, cat_label in CATEGORY_ORDER:
        items = grouped.get(cat_key, [])
        if not items:
            continue
        lines.append(cat_label)
        for item in items:
            lines.append(format_item(item))
        lines.append("")

    lines.append(f"Total open items: {total}")
    return "\n".join(lines)

# ── No items fallback ─────────────────────────────────────────────────────────
def build_empty_message():
    return "Good morning ☀️\n\nNo open items."

# ── Send via Telegram ─────────────────────────────────────────────────────────
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()

# ── Core logic ────────────────────────────────────────────────────────────────
def run_summary():
    items = fetch_open_items()
    if not items:
        message = build_empty_message()
    else:
        grouped = group_by_category(items)
        message = build_message(grouped, total=len(items))
    send_telegram(message)
    return message

if __name__ == "__main__":
    run_summary()