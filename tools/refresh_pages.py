#!/usr/bin/env python3
"""After merging exports: update the month trackers, the day-of-week page and the planner.

Usage:
  python3 tools/refresh_pages.py [--days N]

Steps
  1. Month trackers (Plantation, PBG East, PBG Northlake, Cooper City from Dec):
     for every date in the current month that is in data/mytime.csv, enter
     MyTime's net revenue with update_trackers.py (adds or corrects the day).
     --days N limits this to the last N dates (default: whole month).
  2. Day-of-week page: rebuild DATA_BY_LOC from data/mytime.csv with
     tools/build_dow.py and splice it into day-of-week/index.html. Aborts if
     any row before the current month changed (that would mean a bad export).
  3. Re-apply the MTD/store-tiles section (tools/add_mtd_section.py).
  4. Rebuild planner/index.html (the standalone November MTD Planner copy).

Nothing is committed; review `git diff --stat` and commit yourself.
"""
import csv, json, os, re, subprocess, sys, tempfile, collections, datetime as D

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(REPO, "tools")
DOW = os.path.join(REPO, "day-of-week", "index.html")
TRACKED = {"Plantation": "plantation", "PBG East": "pbg-east", "PBG Northlake": "pbg-northlake", "Cooper City": "cooper-city"}

def loc_name(s):
    return re.split(r" \d", s)[0]

def main(argv):
    days = int(argv[argv.index("--days") + 1]) if "--days" in argv else None
    rows = list(csv.DictReader(open(os.path.join(REPO, "data", "mytime.csv"), encoding="utf-8-sig")))
    dates = [D.datetime.strptime(r["Date"][:10].split(" ")[0], "%m/%d/%Y").date() for r in rows]
    last = max(dates); y, m = last.year, last.month
    net = collections.defaultdict(float)
    for r, d in zip(rows, dates):
        if (d.year, d.month) == (y, m):
            net[(loc_name(r["Location"]), d)] += float(r["Net Revenue"] or 0)

    # 1. trackers
    dow_before = open(DOW).read()
    for name, slug in TRACKED.items():
        ds = sorted(d for (n, d) in net if n == name)
        if days: ds = ds[-days:]
        month_dir = os.path.join(REPO, "" if slug == "plantation" else f"stores/{slug}/", D.date(y, m, 1).strftime("%B").lower())
        if not ds or not os.path.exists(os.path.join(month_dir, "index.html")):
            if ds: print(f"{name}: no {D.date(y,m,1):%B} tracker yet (tools/new_month.py), skipped")
            continue
        for d in ds:
            out = subprocess.run([sys.executable, os.path.join(REPO, "update_trackers.py"), REPO, d.isoformat(), f"{net[(name, d)]:.2f}", slug], capture_output=True, text=True)
            if out.returncode: print(name, d, out.stdout, out.stderr); return 1
        print(f"{name}: tracker updated for {len(ds)} days through {ds[-1]:%m/%d}")
    open(DOW, "w").write(dow_before)  # update_trackers also edits the DOW page; it is rebuilt below instead

    # 2. day-of-week data
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, os.path.join(T, "build_dow.py"), os.path.join(REPO, "data", "mytime.csv"), "--out", tmp, "--year", str(y)], check=True, capture_output=True)
        built = open(os.path.join(tmp, "day-of-week.html")).read()
    mnew = re.search(r"const DATA_BY_LOC = (.*?);\n", built)
    s = open(DOW).read()
    old = json.loads(re.search(r"const DATA_BY_LOC = (.*?);\n", s).group(1)); new = json.loads(mnew.group(1))
    cut = f"{m:02d}"
    changed = [(L, r[0]) for L in old for r in old[L] if r[0] < cut and r not in new.get(L, [])]
    if changed:
        print(f"ABORT: {len(changed)} rows before {cut}/01 changed, e.g. {changed[:5]}. Check the export."); return 1
    s = re.sub(r"const DATA_BY_LOC = .*?;\n", lambda _: "const DATA_BY_LOC = " + mnew.group(1) + ";\n", s, count=1)
    open(DOW, "w").write(s)
    print("day-of-week: data through", {L: new[L][-1][0] for L in new})

    # 3. MTD section
    subprocess.run([sys.executable, os.path.join(T, "add_mtd_section.py"), DOW], check=True)
    # 3b. store health section (membership health + scorecard), from data/mytime.csv
    subprocess.run([sys.executable, os.path.join(T, "add_health_section.py"), DOW], check=True)
    # 4. planner copy
    subprocess.run([sys.executable, os.path.join(T, "build_planner.py")], check=True)
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
