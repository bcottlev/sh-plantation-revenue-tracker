#!/usr/bin/env python3
"""Read every store's end-of-shift Slack channel and record who filed a report each day.

Usage: SLACK_BOT_TOKEN=xoxb-... pull_desk.py [--out desk.json] [--vma "Shenna,Jo"] [--mgr-out mgr.json]

Needs a bot token whose app has been invited to each channel (channels:history /
groups:history). Writes {location: {date: {"desk": [names], "vma": [names]}}}.
Two report formats are handled: forms with a "Date of Report" field, and forms
without one, where the post time (US Eastern) is the report date.
With --mgr-out, also reads the manager report channel(s) into
{location: {date: {"m": name, "net", "dogs", "add", "ret", "nm", "tc", "can", "ld", "tt"}}}.
"""
import os, re, sys, json, time, argparse, datetime, urllib.request, urllib.parse
from zoneinfo import ZoneInfo

CHANNELS = {                      # end-of-shift channels by location
    "Plantation":      "C0A0WQTGTBK",
    "Cooper City":     "C0BE3H9V5C0",
    "Boca Raton West": "C0AK45HC7EW",
    "Boynton Beach":   "C0AKYD6P7UY",
    "Wellington":      "C0AJXP68MBM",
    "West Palm Beach": "C0AJNMGCC4F",
    "Lake Worth":      "C0AJXP1ELHZ",
}
MGR_CHANNELS = {                  # manager revenue report channels by location
    "Plantation": "C0B241EHPP0",  # #broward-leadership
}
ALIAS = {"Nina Mariel": "Nina", "Bryan Cottle": "Bryan"}
ET = ZoneInfo("America/New_York")

def api(token, method, **params):
    req = urllib.request.Request(f"https://slack.com/api/{method}?{urllib.parse.urlencode(params)}",
                                 headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def history(token, channel):
    msgs, cursor = [], None
    joined = False
    while True:
        res = api(token, "conversations.history", channel=channel, limit=200, **({"cursor": cursor} if cursor else {}))
        if not res.get("ok") and res.get("error") in ("not_in_channel", "channel_not_found") and not joined:
            # public channels can be joined by the bot itself; private ones need /invite
            joined = True
            if api(token, "conversations.join", channel=channel).get("ok"): continue
        if not res.get("ok"):
            print(f"  {channel}: {res.get('error')}", file=sys.stderr); return None
        msgs += res.get("messages", [])
        cursor = res.get("response_metadata", {}).get("next_cursor")
        if not cursor: return msgs
        time.sleep(1.2)

_users = {}
def user_name(token, uid):
    if uid not in _users:
        try:
            u = api(token, "users.info", user=uid); p = (u.get("user") or {}).get("profile") or {}
            _users[uid] = p.get("real_name") or p.get("display_name") or uid
        except Exception:
            _users[uid] = uid
    return _users[uid]

def mention_name(token, t, label):
    """Name after a label: <@U..|Name>, a bare <@U..> (resolved via users.info), or plain text."""
    m = re.search(label + r"\s*<@([A-Z0-9]+)(?:\|([^>]+))?>", t)
    if m: return m.group(2) or user_name(token, m.group(1))
    m = re.search(label + r"\s*([A-Za-z][A-Za-z .'-]+)", t)
    return m.group(1) if m else None

def first(name):
    name = name.strip()
    if "," in name:                      # Slack real names can be "Last, First"
        parts = [x.strip() for x in name.split(",") if x.strip()]
        name = parts[1] if len(parts) > 1 else parts[0]
    return ALIAS.get(name, name).rstrip(".").split()[0].strip(",.")

def report_date(m, t):
    d = re.search(r"Date of Report\*?:?\*?\s*(\d{4}-\d{2}-\d{2})", t)
    if d: return d.group(1)
    return datetime.datetime.fromtimestamp(float(m["ts"]), ET).strftime("%Y-%m-%d")

def desk_roster(token, msgs, vma):
    out = {}
    for m in msgs:
        t = m.get("text", "")
        n = mention_name(token, t, r"Name:?\*?:?\*?")
        if not n or "Recap" not in t and "Outreach" not in t: continue
        f = first(n); e = out.setdefault(report_date(m, t), {"desk": [], "vma": [], "stats": {}})
        b = "vma" if f.lower() in vma else "desk"
        if f not in e[b]: e[b].append(f)
        st = e["stats"].setdefault(f, {"o": 0, "l": 0, "d": 0, "a": 0})
        st["o"] += int(num(t, r"Outreach")); st["l"] += int(num(t, r"Leads")); st["d"] += int(num(t, r"Deals Closed")); st["a"] += int(num(t, r"Appointments Booked"))
    return dict(sorted(out.items()))

def num(t, label):
    m = re.search(label + r"[^\n:]*\*?:\*?\s*\$?\s*(-?[\d,]+(?:\.\d+)?)", t)   # "*Label (note)*: 12" and "*Label:*12" both parse
    return float(m.group(1).replace(",", "")) if m else 0.0

def manager_reports(token, msgs):
    best = {}
    for m in msgs:
        t = m.get("text", "")
        if "Net Revenue" not in t: continue
        who = mention_name(token, t, r"Submitted by:?\*?:?\*?")
        rec = {"m": first(who) if who else "", "net": num(t, "Net Revenue"), "dogs": int(num(t, "Dog Visits")),
               "add": int(num(t, "Add-ons Sold")), "ret": num(t, "Retail Sold"), "nm": int(num(t, "New Members")),
               "tc": int(num(t, "Trial Conversions")), "can": int(num(t, "Cancellations")),
               "ld": int(num(t, "New Leads")), "tt": int(num(t, "Trials Booked"))}
        score = sum(1 for k in ("dogs", "add", "ret", "nm", "tc", "can", "ld", "tt") if rec[k])
        key = report_date(m, t); ts = float(m.get("ts", 0))
        if key not in best or (score, ts) > best[key][0]: best[key] = ((score, ts), rec)
    return {k: v[1] for k, v in sorted(best.items())}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="desk.json")
    ap.add_argument("--mgr-out", default="")
    ap.add_argument("--vma", default="Shenna,Jo,Jobeelyn,Cydny,Yana", help="first names of remote VMAs, comma-separated")
    a = ap.parse_args()
    token = os.environ.get("SLACK_BOT_TOKEN", "")
    if not token: sys.exit("SLACK_BOT_TOKEN is not set")
    vma = {v.strip().lower() for v in a.vma.split(",") if v.strip()}
    who = api(token, "auth.test"); print(f"bot: {who.get('user')} ({who.get('user_id')})")

    desk, missing = {}, []
    for locn, ch in CHANNELS.items():
        msgs = history(token, ch)
        if msgs is None: missing.append(locn); continue
        desk[locn] = desk_roster(token, msgs, vma); print(f"{locn}: {len(desk[locn])} days")
    json.dump(desk, open(a.out, "w"), separators=(",", ":"))
    if a.mgr_out:
        mgr = {}
        for locn, ch in MGR_CHANNELS.items():
            msgs = history(token, ch)
            if msgs is None: missing.append(locn + " (manager)"); continue
            mgr[locn] = manager_reports(token, msgs); print(f"{locn} manager: {len(mgr[locn])} days")
        json.dump(mgr, open(a.mgr_out, "w"), separators=(",", ":"))
    if missing: print("bot could not read:", ", ".join(missing), "(public channels are joined automatically; private ones need /invite @<bot>)")

if __name__ == "__main__":
    main()
