#!/usr/bin/env python3
"""Merge MyTime "Revenue Time Series" CSV exports into data/mytime.csv.

Usage:
  python3 tools/merge_exports.py EXPORT.csv [EXPORT2.csv ...] [--drop-open-day]

Rule: each export replaces its own date range for its own locations. Rows for
other locations, and dates outside the export's range, are left alone.

--drop-open-day drops the export's last date when the file was saved before
9 PM Eastern on that date (the store was probably still open). Without it the
script keeps the day and prints a warning so you can decide.
"""
import csv, sys, os, datetime as D, collections
from zoneinfo import ZoneInfo

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(REPO, "data", "mytime.csv")
ET = ZoneInfo("America/New_York")

def dt(s):
    return D.datetime.strptime(s.strip()[:10].split(" ")[0], "%m/%d/%Y").date()

def main(argv):
    drop_open = "--drop-open-day" in argv
    files = [a for a in argv if not a.startswith("--")]
    if not files:
        print(__doc__); return 2
    rows = list(csv.DictReader(open(TARGET, encoding="utf-8-sig")))
    hdr = list(rows[0].keys())
    for f in files:
        new = list(csv.DictReader(open(f, encoding="utf-8-sig")))
        if not new:
            print(f"{f}: empty, skipped"); continue
        miss = [h for h in ("Date", "Location", "Net Revenue") if h not in new[0]]
        if miss:
            print(f"{f}: missing columns {miss}; found {list(new[0])}"); return 2
        lo = min(dt(x["Date"]) for x in new); hi = max(dt(x["Date"]) for x in new)
        saved = D.datetime.fromtimestamp(os.path.getmtime(f), ET)
        if saved.date() == hi and saved.hour < 21:
            if drop_open:
                new = [x for x in new if dt(x["Date"]) != hi]; hi = hi - D.timedelta(days=1)
                print(f"{f}: saved {saved:%I:%M %p} on {saved:%m/%d}; dropped that day (store may still be open)")
            else:
                print(f"WARNING {f}: saved {saved:%I:%M %p} on {saved:%m/%d}, before 9 PM. {hi:%m/%d} may be partial. Re-run with --drop-open-day to leave it out.")
        locs = {x["Location"] for x in new}
        before = len(rows)
        rows = [r for r in rows if not (r["Location"] in locs and lo <= dt(r["Date"]) <= hi)]
        removed = before - len(rows)
        rows += [{h: x.get(h, "") for h in hdr} for x in new]
        per = collections.defaultdict(float)
        for x in new:
            per[(dt(x["Date"]), x["Location"].split(" ")[0])] += float(x["Net Revenue"] or 0)
        print(f"{os.path.basename(f)}: {lo:%m/%d}-{hi:%m/%d}, {len(locs)} locations, replaced {removed} rows with {len(new)}")
    rows.sort(key=lambda r: (dt(r["Date"]), r["Location"]))
    with open(TARGET, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=hdr); w.writeheader(); w.writerows(rows)
    print(f"data/mytime.csv: {len(rows)} rows, through {max(dt(r['Date']) for r in rows):%a %m/%d/%Y}")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
