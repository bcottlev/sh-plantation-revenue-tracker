#!/usr/bin/env python3
"""8 PM end-of-shift report check.

For each store, look for the manager's "End-of-Shift SM Report" for today (and the
last few open days) in the store's revenue-updates channel. Post a reminder in that
channel ONLY when a report is missing; stay silent when everything is in.

  POST=1      actually post (otherwise print what would be posted)
  FOR_DATE    YYYY-MM-DD to check instead of today (America/New_York)
"""
import os, re, json, datetime, urllib.request, urllib.parse
from zoneinfo import ZoneInfo

TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
POST = os.environ.get("POST") == "1"
LOOKBACK = 7   # also flag earlier open days still missing within this many days

# store -> (channel the report is submitted to, Slack ids to tag, weekdays closed: Mon=0..Sun=6)
STORES = {
    "Plantation":    ("C0C9WCYKX8A", os.environ.get("TAG_PLANTATION", ""), set()),
    "PBG East":      ("C0CBZGMS9MW", os.environ.get("TAG_PBG", ""), set()),
    "PBG Northlake": ("C0CBZGMS9MW", os.environ.get("TAG_PBG", ""), {6}),
}
# every channel a manager report has ever been posted to (a report anywhere counts)
REPORT_CHANNELS = ["C0C9WCYKX8A", "C0CBZGMS9MW", "C0CAZSK43V3", "C0B241EHPP0"]
HOLIDAYS = {"2026-11-26", "2026-12-25", "2027-01-01"}   # all stores closed

def api(method, http="GET", **params):
    if http == "POST":
        req = urllib.request.Request(f"https://slack.com/api/{method}", data=json.dumps(params).encode(),
                                     headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json; charset=utf-8"})
    else:
        req = urllib.request.Request(f"https://slack.com/api/{method}?{urllib.parse.urlencode(params)}",
                                     headers={"Authorization": f"Bearer {TOKEN}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def scenter_of(t):
    m = re.search(r"Scenter:?\*?:?\*?\s*([A-Za-z][A-Za-z ]+?)\s*(?:\n|\*|$)", t) or re.search(r"Report\s+([A-Za-z][A-Za-z ]+?)\s*:", t)
    name = m.group(1).strip() if m else "Plantation"
    for k in STORES:
        if name.lower().startswith(k.lower()): return k
    return name

def reported(oldest_ts):
    """{(store, 'YYYY-MM-DD')} for every manager report posted since oldest_ts."""
    got = set()
    for ch in REPORT_CHANNELS:
        cursor = None
        while True:
            res = api("conversations.history", channel=ch, oldest=oldest_ts, limit=200, **({"cursor": cursor} if cursor else {}))
            if not res.get("ok"):
                print(f"{ch}: {res.get('error')}"); break
            for m in res.get("messages", []):
                t = m.get("text", "")
                d = re.search(r"Date of Report\*?:?\*?\s*(\d{4}-\d{2}-\d{2})", t)
                if d and "Net Revenue" in t:
                    got.add((scenter_of(t), d.group(1)))
            cursor = res.get("response_metadata", {}).get("next_cursor")
            if not cursor: break
    return got

def open_on(store, day):
    return day.isoformat() not in HOLIDAYS and day.weekday() not in STORES[store][2]

def label(day):
    return day.strftime("%a %-m/%-d")

tz = ZoneInfo("America/New_York")
today = datetime.date.fromisoformat(os.environ["FOR_DATE"]) if os.environ.get("FOR_DATE") else datetime.datetime.now(tz).date()
start = max(today - datetime.timedelta(days=LOOKBACK), today.replace(day=1) - datetime.timedelta(days=1))
oldest = datetime.datetime.combine(start, datetime.time(0), tz).timestamp()
have = reported(f"{oldest:.0f}")
print(f"checking {today} (back to {start}); reports found: {sorted(have)}")

for store, (channel, tags, _) in STORES.items():
    days = [start + datetime.timedelta(days=i) for i in range((today - start).days + 1)]
    missing = [d for d in days if open_on(store, d) and (store, d.isoformat()) not in have]
    if not missing:
        print(f"{store}: all reports in - no message"); continue
    tag = " ".join(f"<@{u}>" for u in tags.split(",") if u.strip())
    today_missing = missing[-1] == today
    earlier = [d for d in missing if d != today]
    lines = [f"⏰ *{store} · End-of-shift report missing*" + (f" {tag}" if tag else "")]
    if today_missing:
        lines.append(f"Today's report ({label(today)}) hasn't been submitted yet. Please submit it before you leave tonight.")
    if earlier:
        lines.append(("Also still missing: " if today_missing else "Still missing: ") + ", ".join(label(d) for d in earlier) + ".")
    text = "\n".join(lines)
    print(f"--- {store} -> {channel}\n{text}")
    if POST:
        r = api("chat.postMessage", http="POST", channel=channel, text=text, unfurl_links=False)
        print("posted" if r.get("ok") else f"::error::post failed: {r.get('error')}")
