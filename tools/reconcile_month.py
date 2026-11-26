#!/usr/bin/env python3
"""Month-end reconciliation from a MyTime Revenue Time Series CSV.

Usage: reconcile_month.py REPO_DIR CSV_PATH

- Rebuilds the DATA array in day-of-week/index.html from MyTime (net, non-membership
  split, batch flag) for every date present in the CSV. Dates not in the CSV are kept.
- Rewrites every fully covered month in month_totals.json with true totals/splits.
- Overwrites dailyRevenue in each month tracker whose dates appear in the CSV, so the
  tracker matches MyTime (tickets that closed after the EOS report get captured).
Prints a per-month comparison of tracker vs MyTime so the difference can be reported.
"""
import sys, csv, json, re, os, datetime, collections, calendar

repo, csv_path = sys.argv[1], sys.argv[2]
def f(v):
    v = (v or '').strip().replace(',', '').replace('$', '')
    try: return float(v)
    except: return 0.0

daily = collections.defaultdict(lambda: {'net': 0.0, 'memb': 0.0})
with open(csv_path, encoding='utf-8-sig') as fh:
    for r in csv.DictReader(fh):
        ds = r['Date'].strip()
        if not ds: continue
        dt = datetime.datetime.strptime(ds, '%m/%d/%Y').date()
        daily[dt]['net'] += f(r['Net Revenue'])
        daily[dt]['memb'] += f(r['Memberships']) + f(r['Membership Discounts'])

# ---- day-of-week DATA ----------------------------------------------------
dow_file = os.path.join(repo, 'day-of-week', 'index.html')
d = open(dow_file).read()
multi = re.search(r"const DATA_BY_LOC = (\{.*?\});\n", d, re.S)
m = multi or re.search(r"const DATA = (\[\[.*?\]\]);", d, re.S)
store = json.loads(m.group(1))
data = {r[0]: r for r in (store["Plantation"] if multi else store)}
for dt, v in daily.items():
    net = round(v['net'], 2); memb = round(v['memb'], 2)
    data[dt.strftime('%m-%d')] = [dt.strftime('%m-%d'), dt.weekday(), net, round(net - memb, 2), 1 if memb > 1500 else 0]
rows = [data[k] for k in sorted(data)]
if multi: store["Plantation"] = rows
d = d[:m.start(1)] + json.dumps(store if multi else rows, separators=(',', ':')) + d[m.end(1):]
open(dow_file, 'w').write(d)

# ---- month totals + trackers --------------------------------------------
months = collections.defaultdict(list)
for dt in daily: months[dt.strftime('%Y-%m')].append(dt)
totals_path = os.path.join(repo, 'month_totals.json')
totals = json.load(open(totals_path)) if os.path.exists(totals_path) else {}
report = {}
for ym, dts in months.items():
    y, mo = map(int, ym.split('-'))
    full = max(dts).day == calendar.monthrange(y, mo)[1]
    net = sum(daily[x]['net'] for x in dts); memb = sum(daily[x]['memb'] for x in dts)
    if full:
        totals[ym] = {"total": round(net, 2), "membership": round(memb, 2),
                      "non_membership": round(net - memb, 2), "active_days": len([x for x in dts if daily[x]['net'] > 0])}
    # tracker
    mf = os.path.join(repo, datetime.date(y, mo, 1).strftime('%B').lower(), 'index.html')
    tracker_total = None
    mm = None
    if os.path.exists(mf):
        s = open(mf).read()
        mm = re.search(r"const dailyRevenue = \{\n(.*?)\n(\s*)\};", s, re.S)
    if mm:
        old = {}
        for line in mm.group(1).splitlines():
            x = re.match(r"\s*'(\d{4}-\d{2}-\d{2})':\s*([\d.]+)", line)
            if x: old[x.group(1)] = float(x.group(2))
        tracker_total = round(sum(old.values()), 2)
        for x in dts:
            if daily[x]['net'] != 0: old[x.isoformat()] = round(daily[x]['net'], 2)
        indent = re.match(r"(\s*)'", mm.group(1)).group(1) if mm.group(1).strip() else mm.group(2) + "    "
        s = s[:mm.start(1)] + ",\n".join(f"{indent}'{k}': {v:.2f}" for k, v in sorted(old.items())) + s[mm.end(1):]
        open(mf, 'w').write(s)
    report[ym] = {"mytime_net": round(net, 2), "membership": round(memb, 2), "non_membership": round(net - memb, 2),
                  "tracker_before": tracker_total, "full_month": bool(full)}
json.dump(totals, open(totals_path, 'w'), indent=2)
print(json.dumps(report, indent=2))
