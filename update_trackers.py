#!/usr/bin/env python3
"""Enter (or correct) one day's net revenue in both trackers.

Usage: update_trackers.py REPO_DIR YYYY-MM-DD AMOUNT

Edits:
  <month>/index.html      -> dailyRevenue object (adds or replaces the date)
  day-of-week/index.html  -> DATA array (adds or replaces the date)

Prints a JSON summary: mtd, days_entered, target, days_remaining, need_per_day.
Exits 2 if the month tracker file does not exist yet (see SKILL.md for rollover).
"""
import sys, re, json, os, datetime, calendar

STORES = {  # slug -> (display name, directory under the repo; Plantation keeps the root for history)
    "plantation":    ("Plantation",    ""),
    "pbg-east":      ("PBG East",      "stores/pbg-east/"),
    "pbg-northlake": ("PBG Northlake", "stores/pbg-northlake/"),
    "cooper-city":   ("Cooper City",   "stores/cooper-city/"),
}
repo, date_s, amount_s = sys.argv[1], sys.argv[2], sys.argv[3]
store = sys.argv[4] if len(sys.argv) > 4 else "plantation"
if store not in STORES:
    print(json.dumps({"error": f"unknown store '{store}'; use one of {list(STORES)}"})); sys.exit(2)
store_name, store_dir = STORES[store]
amount = round(float(amount_s.replace('$','').replace(',','')), 2)
dt = datetime.date.fromisoformat(date_s)
month_dir = os.path.join(repo, store_dir, dt.strftime('%B').lower())
month_file = os.path.join(month_dir, 'index.html')
dow_file = os.path.join(repo, 'day-of-week', 'index.html')

if not os.path.exists(month_file):
    print(json.dumps({"error": f"missing {month_file}; create the {store_name} month tracker first (new_month.py)"}))
    sys.exit(2)

# ---- month tracker -------------------------------------------------------
s = open(month_file).read()
m = re.search(r"const dailyRevenue = \{(.*?)\n(\s*)\};", s, re.S)   # body may be empty on a fresh month
if not m:
    print(json.dumps({"error": "dailyRevenue block not found"})); sys.exit(1)
body, indent_close = m.group(1).lstrip("\n"), m.group(2)
entries = {}
for line in body.splitlines():
    mm = re.match(r"\s*'(\d{4}-\d{2}-\d{2})':\s*([\d.]+)", line)
    if mm: entries[mm.group(1)] = float(mm.group(2))
replaced = date_s in entries
entries[date_s] = amount
indent = re.match(r"(\s*)'", body).group(1) if body.strip() else indent_close + "    "
new_body = ",\n".join(f"{indent}'{d}': {v:.2f}" for d, v in sorted(entries.items()))
s = s[:m.start(1)] + "\n" + new_body + s[m.end(1):]
open(month_file, 'w').write(s)

target = float(re.search(r"const targetTotal = ([\d.]+);", s).group(1))

# ---- day-of-week page ----------------------------------------------------
d = open(dow_file).read()
# the page is either single-store (const DATA = [[...]]) or multi-store (const DATA_BY_LOC = {"Plantation": [[...]], ...})
multi = re.search(r"const DATA_BY_LOC = (\{.*?\});\n", d, re.S)
m2 = multi or re.search(r"const DATA = (\[\[.*?\]\]);", d, re.S)
page = json.loads(m2.group(1))
if multi and store_name not in page: page[store_name] = []   # a new store appears on the page with its first entry
data = page[store_name] if multi else page
key = dt.strftime('%m-%d')
# batch flag: membership billing runs on the 1st; flag it so the membership view excludes it
batch = 1 if dt.day == 1 else 0
row = [key, dt.weekday(), amount, None, batch]
idx = next((i for i, r in enumerate(data) if r[0] == key), None)
if idx is None:
    data.append(row)
else:
    # keep an existing non-membership split if MyTime already supplied one
    row[3] = data[idx][3]; data[idx] = row
data.sort(key=lambda r: r[0])
if multi: page[store_name] = data; page = dict(sorted(page.items()))   # the page lists stores alphabetically
d = d[:m2.start(1)] + json.dumps(page if multi else data, separators=(',', ':')) + d[m2.end(1):]
open(dow_file, 'w').write(d)

# ---- summary -------------------------------------------------------------
days_in_month = calendar.monthrange(dt.year, dt.month)[1]
mtd = sum(entries.values())
entered = len(entries)
last_day = max(datetime.date.fromisoformat(k) for k in entries).day
remaining = days_in_month - last_day
print(json.dumps({
    "store": store_name, "date": date_s, "amount": amount, "replaced_existing": replaced,
    "mtd": round(mtd, 2), "days_entered": entered, "target": target,
    "days_remaining": remaining,
    "need_per_day": round((target - mtd) / remaining, 2) if remaining else None,
    "month_file": month_file
}))
