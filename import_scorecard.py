#!/usr/bin/env python3
"""Import the FBC "Scenter Scorecard" export (Power BI -> Excel) into data/scorecard.json
and the day-of-week page (const SC_BY_LOC).

Usage: python3 import_scorecard.py Scenter_Scorecard.xlsx [--year 2026] [--loc Plantation]

The export has one column per day ("Mon (10/19)") plus MTD Avg / Prior Month Avg, and
one row per metric. The location comes from the "Applied filters" footer unless --loc is given.
Re-importing overwrites the same dates; other dates are kept.
"""
import sys, re, json, os, argparse, openpyxl

KEYS = {"Dog Visits": "dogs", "Add-on Revenue": "addrev", "Avg Ticket Value": "atv", "Attachment Rate": "att",
        "SCENT Check": "scent", "Rebook Rate": "rebook", "Calendar Utilization": "util",
        "Trials/ First Visits": "trials", "Same Day Conversion": "sdc", "New Members": "nm",
        "No Show": "noshow", "Cancellations": "can", "Active Members": "active", "Scenter Revenue": "rev"}

def val(s):
    s = (s or "").strip().replace("​", "")
    if not s: return None
    s = s.replace("$", "").replace(",", "")
    try: return float(s.rstrip("%"))
    except ValueError: return None

ap = argparse.ArgumentParser(); ap.add_argument("xlsx"); ap.add_argument("--year", type=int, default=2026); ap.add_argument("--loc", default="")
a = ap.parse_args()
ws = openpyxl.load_workbook(a.xlsx, data_only=True).worksheets[0]
rows = [[("" if c is None else str(c)) for c in r] for r in ws.iter_rows(values_only=True)]
hdr = rows[0]
loc = a.loc
if not loc:
    foot = " ".join(r[0] for r in rows if "location_name is" in r[0])
    m = re.search(r"location_name is ([^\n]+)", foot); loc = m.group(1).strip() if m else "Plantation"
cols = {}
for i, h in enumerate(hdr):
    m = re.search(r"\((\d{1,2})/(\d{1,2})\)", h)
    if m: cols[i] = f"{a.year}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
days = {d: {} for d in cols.values()}
for r in rows:
    k = KEYS.get(r[0].strip())
    if not k: continue
    for i, d in cols.items():
        v = val(r[i] if i < len(r) else "")
        if v is not None: days[d][k] = int(v) if k in ("dogs", "trials", "nm", "noshow", "can", "active") else v

path = "data/scorecard.json"
allsc = json.load(open(path)) if os.path.exists(path) else {}
allsc.setdefault(loc, {}).update(days)
allsc[loc] = dict(sorted(allsc[loc].items()))
json.dump(allsc, open(path, "w"), indent=1)

page = "day-of-week/index.html"
s = open(page).read()
blob = json.dumps(allsc, separators=(",", ":"))
if "const SC_BY_LOC = " in s:
    s = re.sub(r"const SC_BY_LOC = \{.*?\};\n", lambda m: f"const SC_BY_LOC = {blob};\n", s, count=1, flags=re.S)
else:
    s = s.replace("const MGR_BY_LOC = ", f"const SC_BY_LOC = {blob};\nconst MGR_BY_LOC = ", 1)
open(page, "w").write(s)
print(json.dumps({"loc": loc, "dates": sorted(days), "latest": days[max(days)] if days else {}}))
