#!/usr/bin/env python3
"""Read #plantation-end-of-shift and record who submitted a report each day.

Writes the roster into day-of-week/index.html as `const DESK = {...};` keyed by
YYYY-MM-DD -> {"desk": [names], "vma": [names]}. VMAs (remote member associates)
are listed separately from in-store front desk staff.
"""
import os, re, sys, json, time, urllib.request, urllib.parse

TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
CHANNEL = "C0A0WQTGTBK"          # plantation-end-of-shift
VMA = {"shenna", "jo"}           # remote virtual member associates
PAGE = "day-of-week/index.html"

def api(method, **params):
    q = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"https://slack.com/api/{method}?{q}", headers={"Authorization": f"Bearer {TOKEN}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

msgs, cursor = [], None
while True:
    res = api("conversations.history", channel=CHANNEL, limit=200, **({"cursor": cursor} if cursor else {}))
    if not res.get("ok"):
        open("eos_error.txt","w").write(f"slack error: {res.get('error')} (token present: {bool(TOKEN)}, len {len(TOKEN)})\n")
        print("slack error:", res.get("error")); sys.exit(1)
    msgs += res.get("messages", [])
    cursor = res.get("response_metadata", {}).get("next_cursor")
    if not cursor: break
    time.sleep(1.2)

roster = {}
for m in msgs:
    t = m.get("text", "")
    d = re.search(r"Date of Report\*?:?\*?\s*(\d{4}-\d{2}-\d{2})", t)
    n = re.search(r"Name:?\*?:?\s*<@[A-Z0-9]+\|([^>]+)>", t) or re.search(r"Name:?\*?:?\s*([A-Za-z][A-Za-z .'-]+)", t)
    if not (d and n): continue
    name = n.group(1).strip().rstrip(".")
    first = name.split()[0]
    entry = roster.setdefault(d.group(1), {"desk": [], "vma": []})
    bucket = "vma" if first.lower() in VMA else "desk"
    if first not in entry[bucket]: entry[bucket].append(first)

s = open(PAGE).read()
new = "const DESK = " + json.dumps(dict(sorted(roster.items())), separators=(",", ":")) + ";"
if "const DESK = " in s:
    s = re.sub(r"const DESK = \{.*?\};", new, s, count=1, flags=re.S)
else:
    s = s.replace("const DATA = ", new + "\nconst DATA = ", 1)
open(PAGE, "w").write(s)
print(f"{len(msgs)} messages scanned, {len(roster)} days with reports, {min(roster)} to {max(roster)}")
