#!/usr/bin/env python3
"""Read the two end-of-shift channels and embed who worked / what happened each day
into day-of-week/index.html.

  #plantation-end-of-shift (C0A0WQTGTBK): member associate reports -> DESK
      {date: {"desk": [in-store names], "vma": [remote VMA names]}}
  #broward-leadership (C0B241EHPP0): manager revenue reports -> MGR
      {date: {"m": manager, "dogs": n, "add": n, "ret": $, "nm": n, "tc": n, "can": n, "ld": n, "tt": n, "net": $}}

If a channel cannot be read (bot not a member), that block is left untouched.
"""
import os, re, sys, json, time, urllib.request, urllib.parse

TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
PAGE = "day-of-week/index.html"
VMA = {"shenna", "jo"}
ALIAS = {"Nina Mariel": "Nina", "Bryan Cottle": "Bryan"}

def api(method, **params):
    q = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"https://slack.com/api/{method}?{q}", headers={"Authorization": f"Bearer {TOKEN}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def history(channel):
    msgs, cursor = [], None
    while True:
        res = api("conversations.history", channel=channel, limit=200, **({"cursor": cursor} if cursor else {}))
        if not res.get("ok"):
            print(f"{channel}: slack error {res.get('error')}"); status.append(f"{channel}: {res.get('error')}"); return None
        msgs += res.get("messages", [])
        cursor = res.get("response_metadata", {}).get("next_cursor")
        if not cursor: return msgs
        time.sleep(1.2)

def first(name):
    name = ALIAS.get(name.strip(), name.strip()).rstrip(".")
    return name.split()[0]

def num(t, label):
    m = re.search(label + r"[^\n]*?:\s*\$?\s*(-?[\d,]+(?:\.\d+)?)", t)
    return float(m.group(1).replace(",", "")) if m else 0.0

def desk_roster(msgs):
    out = {}
    for m in msgs:
        t = m.get("text", "")
        d = re.search(r"Date of Report\*?:?\*?\s*(\d{4}-\d{2}-\d{2})", t)
        n = re.search(r"Name:?\*?:?\s*<@[A-Z0-9]+\|([^>]+)>", t) or re.search(r"Name:?\*?:?\s*([A-Za-z][A-Za-z .'-]+)", t)
        if not (d and n): continue
        f = first(n.group(1)); e = out.setdefault(d.group(1), {"desk": [], "vma": []})
        b = "vma" if f.lower() in VMA else "desk"
        if f not in e[b]: e[b].append(f)
    return out

def manager_reports(msgs):
    best = {}
    for m in msgs:
        t = m.get("text", "")
        d = re.search(r"Date of Report:?\s*(\d{4}-\d{2}-\d{2})", t)
        if not d or "Net Revenue" not in t: continue
        who = re.search(r"Submitted by:\s*(?:<@[A-Z0-9]+\|)?([A-Za-z][A-Za-z .'-]*)", t)
        rec = {"m": first(who.group(1)) if who else "", "net": num(t, "Net Revenue"), "dogs": int(num(t, "Dog Visits")),
               "add": int(num(t, "Add-ons Sold")), "ret": num(t, "Retail Sold"), "nm": int(num(t, "New Members")),
               "tc": int(num(t, "Trial Conversions")), "can": int(num(t, "Cancellations")),
               "ld": int(num(t, "New Leads")), "tt": int(num(t, "Trials Booked"))}
        score = sum(1 for k in ("dogs", "add", "ret", "nm", "tc", "can", "ld", "tt") if rec[k])
        key = d.group(1); ts = float(m.get("ts", 0))
        if key not in best or (score, ts) > best[key][0]: best[key] = ((score, ts), rec)
    return {k: v[1] for k, v in best.items()}

def inject(s, const, data):
    line = f"const {const} = " + json.dumps(dict(sorted(data.items())), separators=(",", ":")) + ";"
    if f"const {const} = " in s:
        return re.sub(rf"const {const} = \{{.*?\}};", line, s, count=1, flags=re.S)
    return s.replace("const DATA = ", line + "\nconst DATA = ", 1)

status = []
try:
    who = api("auth.test"); status.append(f"bot: {who.get('user')} (app user id {who.get('user_id')}) in workspace {who.get('team')}")
except Exception as e:
    status.append(f"auth.test failed: {e}")
s = open(PAGE).read()
eos = history("C0A0WQTGTBK")
if eos is not None:
    r = desk_roster(eos); s = inject(s, "DESK", r); print(f"DESK: {len(r)} days")
lead = history("C0B241EHPP0")
if lead is not None:
    r = manager_reports(lead); s = inject(s, "MGR", r); print(f"MGR: {len(r)} days")
open(PAGE, "w").write(s)
open("eos_status.txt", "w").write("\n".join(status) + "\n")
if eos is None and lead is None: sys.exit(1)
