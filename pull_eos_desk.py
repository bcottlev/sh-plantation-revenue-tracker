#!/usr/bin/env python3
# channels: plantation/pbg/cooper-city revenue updates + broward-pbg-leadership (bot invited 2026-10-23)
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
VMA = {"shenna", "jo", "jobeelyn", "cydny", "yana"}   # remote virtual member associates (Jo = Jobeelyn Agustin)
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

_users = {}
def user_name(uid):
    if uid not in _users:
        try:
            u = api("users.info", user=uid)
            p = (u.get("user") or {}).get("profile") or {}
            _users[uid] = p.get("real_name") or p.get("display_name") or (u.get("user") or {}).get("real_name") or uid
        except Exception:
            _users[uid] = uid
    return _users[uid]

def mention_name(t, label):
    """Name after a label: either <@U..|Name>, a bare <@U..> (resolved via users.info), or plain text."""
    m = re.search(label + r"\s*<@([A-Z0-9]+)(?:\|([^>]+))?>", t)
    if m: return m.group(2) or user_name(m.group(1))
    m = re.search(label + r"\s*([A-Za-z][A-Za-z .'-]+)", t)
    return m.group(1) if m else None

def first(name):
    name = name.strip()
    if "," in name:                      # "Agustin, Jo" -> "Jo"
        parts = [x.strip() for x in name.split(",") if x.strip()]
        name = parts[1] if len(parts) > 1 else parts[0]
    name = ALIAS.get(name, name).rstrip(".")
    return name.split()[0].strip(",.")

def num(t, label):
    m = re.search(label + r"[^\n:]*\*?:\*?\s*\$?\s*(-?[\d,]+(?:\.\d+)?)", t)   # "*Label (note)*: 12" and "*Label:*12" both parse
    return float(m.group(1).replace(",", "")) if m else 0.0

def desk_roster(msgs):
    out = {}
    for m in msgs:
        t = m.get("text", "")
        d = re.search(r"Date of Report\*?:?\*?\s*(\d{4}-\d{2}-\d{2})", t)
        n = mention_name(t, r"Name:?\*?:?\*?")
        if not (d and n): continue
        f = first(n); e = out.setdefault(d.group(1), {"desk": [], "vma": [], "stats": {}})
        b = "vma" if f.lower() in VMA else "desk"
        if f not in e[b]: e[b].append(f)
        # per-person productivity from the form: outreach, leads, deals closed, appointments booked
        st = e["stats"].setdefault(f, {"o": 0, "l": 0, "d": 0, "a": 0})
        st["o"] += int(num(t, r"Outreach")); st["l"] += int(num(t, r"Leads")); st["d"] += int(num(t, r"Deals Closed")); st["a"] += int(num(t, r"Appointments Booked"))
    return out

SCENTER_SLUG = {"Plantation": "plantation", "PBG East": "pbg-east", "PBG Northlake": "pbg-northlake", "Cooper City": "cooper-city"}

def scenter_of(t):
    # "*Scenter:* PBG East" (older form) or "End-of-Shift SM Report PBG East:" (per-channel form, Oct 2026)
    m = re.search(r"Scenter:?\*?:?\*?\s*([A-Za-z][A-Za-z ]+?)\s*(?:\n|\*|$)", t) or re.search(r"Report\s+([A-Za-z][A-Za-z ]+?)\s*:", t)
    name = m.group(1).strip() if m else "Plantation"
    for k in SCENTER_SLUG:
        if name.lower().startswith(k.lower()): return k
    return name

def manager_reports(msgs, scenter="Plantation"):
    best = {}
    for m in msgs:
        t = m.get("text", "")
        d = re.search(r"Date of Report\*?:?\*?\s*(\d{4}-\d{2}-\d{2})", t)
        if not d or "Net Revenue" not in t: continue
        if scenter_of(t) != scenter: continue
        who = mention_name(t, r"Submitted by:?\*?:?\*?")
        rec = {"m": first(who) if who else "", "net": num(t, "Net Revenue"), "dogs": int(num(t, "Dog Visits")),
               "add": int(num(t, "Add-ons Sold")), "ret": num(t, "Retail Sold"), "nm": int(num(t, "New Members")),
               "tc": int(num(t, "Trial Conversions")), "can": int(num(t, "Cancellations")),
               "ld": int(num(t, "New Leads")), "tt": int(num(t, "Trials Booked"))}
        score = sum(1 for k in ("dogs", "add", "ret", "nm", "tc", "can", "ld", "tt") if rec[k])
        key = d.group(1); ts = float(m.get("ts", 0))
        if key not in best or (score, ts) > best[key][0]: best[key] = ((score, ts), rec)
    return {k: v[1] for k, v in best.items()}

def inject(s, const, data):
    """Write into the multi-store page (DESK_BY_LOC / MGR_BY_LOC keyed by location) or the single-store page."""
    multi = f"const {const}_BY_LOC = "
    if multi in s:
        m = re.search(rf"const {const}_BY_LOC = (\{{.*?\}});\n", s, re.S)
        cur = json.loads(m.group(1)); cur["Plantation"] = dict(sorted(data.items()))
        return s[:m.start(1)] + json.dumps(cur, separators=(",", ":")) + s[m.end(1):]
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
    r = desk_roster(eos); print(f"DESK: {len(r)} days")
    if r: s = inject(s, "DESK", r)
# manager end-of-shift reports: the per-scenter revenue channels (since Oct 21 2026) plus the leadership channel for history
lead = []
for ch in ("C0C9WCYKX8A", "C0CBZGMS9MW", "C0CAZSK43V3", "C0B241EHPP0"):   # plantation-, pbg-, cooper-city-revenue-updates, broward-pbg-leadership
    h = history(ch)
    if h is None: status.append(f"{ch}: not readable (invite @plantation_revenue_bo)")
    else: lead += h
if not lead: lead = None
if lead is not None:
    r = manager_reports(lead); print(f"MGR: {len(r)} days")
    if r: s = inject(s, "MGR", r)
open(PAGE, "w").write(s)

# ---- fill the month trackers from the manager reports: a date the tracker doesn't have yet gets the
# manager's Net Revenue, so the morning Slack report never lags the end-of-shift form. Hand entries win;
# a correction still goes through update_trackers.py by hand.
import subprocess, datetime
STORE_DIR = {"plantation": "", "pbg-east": "stores/pbg-east/", "pbg-northlake": "stores/pbg-northlake/", "cooper-city": "stores/cooper-city/"}
filled = []
if lead is not None:
    for scenter, slug in SCENTER_SLUG.items():
        reps = manager_reports(lead, scenter)
        for d, rec in sorted(reps.items()):
            if rec["net"] <= 0: continue
            dt = datetime.date.fromisoformat(d)
            mf = os.path.join(STORE_DIR[slug], dt.strftime("%B").lower(), "index.html")
            if not os.path.exists(mf): continue
            have = re.findall(r"'(\d{4}-\d{2}-\d{2})':\s*[\d.]+", open(mf).read())
            if d in have: continue
            r = subprocess.run([sys.executable, "update_trackers.py", ".", d, f"{rec['net']:.2f}", slug], capture_output=True, text=True)
            filled.append(f"{scenter} {d} ${rec['net']:.2f}" + ("" if r.returncode == 0 else f" FAILED: {r.stdout.strip()} {r.stderr.strip()}"))
if filled: status.append("filled from manager reports: " + "; ".join(filled)); print("FILLED:", *filled, sep="\n  ")
open("eos_status.txt", "w").write("\n".join(status) + "\n")
if eos is None and lead is None: sys.exit(1)
