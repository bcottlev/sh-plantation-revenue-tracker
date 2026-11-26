#!/usr/bin/env python3
"""Build day-of-week revenue pages from a MyTime Revenue Time Series CSV.

Usage:
  build_dow.py CSV [CSV ...] [--out DIR] [--name day-of-week.html]
                   [--locations "Plantation,Boca Raton West"] [--year 2026]
                   [--desk desk.json] [--mgr mgr.json] [--bad 500 --great 1000]

The CSV(s) may cover one location or many; rows are split on the Location column.
Every location found (or only those named with --locations) goes into ONE page with a
location toggle; a comparison table of every location sits at the bottom of that page.
--desk desk.json and --mgr mgr.json (from pull_desk.py) add who filed each day's
end-of-shift report, and the manager's numbers, to the dot tooltips.

Per-day figures: net revenue (after discounts/prepaids/refunds) and non-membership
revenue (net minus Memberships and Membership Discounts). Bulk membership billing
days are flagged so the page can exclude them from the membership-inclusive view.
"""
import argparse, csv, json, os, re, sys, datetime, collections, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "assets", "template.html")

def money(v):
    return f"${v:,.0f}"

def fnum(v):
    v = (v or "").strip().replace(",", "").replace("$", "")
    try: return float(v)
    except ValueError: return 0.0

def slugify(name):
    # "Plantation 8126 W Broward Blvd" -> "plantation"; "Boca Raton West 123 ..." -> "boca-raton-west"
    words = []
    for w in name.split():
        if re.match(r"^\d", w): break
        words.append(w)
    return re.sub(r"[^a-z0-9]+", "-", " ".join(words).lower()).strip("-") or "location"

def display(name):
    words = []
    for w in name.split():
        if re.match(r"^\d", w): break
        words.append(w)
    return " ".join(words) or name

def load(csv_paths):
    daily = collections.defaultdict(lambda: collections.defaultdict(lambda: {"net": 0.0, "memb": 0.0}))
    for p in csv_paths:
        with open(p, encoding="utf-8-sig") as fh:
            r = csv.DictReader(fh)
            need = {"Date", "Net Revenue"}
            if not need <= set(r.fieldnames or []):
                sys.exit(f"{p}: expected MyTime Revenue Time Series columns (Date, Net Revenue, ...), got {r.fieldnames}")
            for row in r:
                d = (row.get("Date") or "").strip()
                if not d: continue
                try: dt = datetime.datetime.strptime(d, "%m/%d/%Y").date()
                except ValueError: continue
                loc = (row.get("Location") or "All").strip()
                daily[loc][dt]["net"] += fnum(row.get("Net Revenue"))
                daily[loc][dt]["memb"] += fnum(row.get("Memberships")) + fnum(row.get("Membership Discounts"))
    return daily

def records(days):
    """[["MM-DD", weekday, net, nonmemb, batch], ...] sorted by date."""
    memb_days = [v["memb"] for v in days.values() if v["memb"] > 0]
    med = statistics.median(memb_days) if memb_days else 0
    cutoff = max(1500.0, 4 * med)
    out = []
    for dt in sorted(days):
        net = round(days[dt]["net"], 2); memb = round(days[dt]["memb"], 2)
        out.append([dt.strftime("%m-%d"), dt.weekday(), net, round(net - memb, 2), 1 if memb > cutoff else 0])
    return out

def build_page(items, year, out_path, tpl, bad, great, desk, mgr, default_loc="Plantation", vwc="Shenna,Jo,Jobeelyn"):
    """items: [(display name, recs)]. One page with a location toggle."""
    names = [n for n, _ in items]
    data = {n: r for n, r in items}
    def pick(src): return {n: src.get(n, {}) for n in names}
    html = (tpl.replace("__TITLE__", f"Scenthound {names[0]} — Daily Revenue Tracker")
               .replace("__DESK__", json.dumps(pick(desk), separators=(",", ":")))
               .replace("__MGR__", json.dumps(pick(mgr), separators=(",", ":")))
               .replace("__DATA__", json.dumps(data, separators=(",", ":")))
               .replace("__YEAR__", str(year)).replace("__DEFAULT_LOC__", default_loc)
               .replace("__BAD__", str(bad)).replace("__GREAT__", str(great))
               .replace("__VWC__", json.dumps([v.strip().lower() for v in vwc.split(",") if v.strip()])))
    open(out_path, "w").write(html)
    return out_path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="+")
    ap.add_argument("--out", default="/mnt/user-data/outputs")
    ap.add_argument("--locations", default="", help="comma-separated display names to include (prefix match, case-insensitive)")
    ap.add_argument("--default", dest="default_loc", default="Plantation", help="store the page opens on")
    ap.add_argument("--year", type=int, default=datetime.date.today().year)
    ap.add_argument("--name", default="day-of-week.html", help="output file name")
    ap.add_argument("--desk", default="", help="desk.json from pull_desk.py")
    ap.add_argument("--mgr", default="", help="mgr.json from pull_desk.py --mgr-out")
    ap.add_argument("--bad", type=int, default=500, help="daily revenue below this is flagged red")
    ap.add_argument("--great", type=int, default=1000, help="daily revenue at or above this is flagged green")
    ap.add_argument("--vwc", default="Shenna,Jo,Jobeelyn,Cydny,Yana", help="first names of remote VWCs, comma-separated (labels the outreach table)")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    tpl = open(TEMPLATE).read()
    daily = load(a.csv)
    want = [w.strip().lower() for w in a.locations.split(",") if w.strip()]
    items = []
    for loc in sorted(daily):
        if want and not any(display(loc).lower().startswith(w) for w in want): continue
        recs = records(daily[loc]); name = display(loc)
        items.append((name, recs))
        print(f"{name}: {len(recs)} days, {recs[0][0]} to {recs[-1][0]}")
    if not items:
        sys.exit("no locations matched")
    desk = json.load(open(a.desk)) if a.desk else {}
    mgr = json.load(open(a.mgr)) if a.mgr else {}
    out = build_page(items, a.year, os.path.join(a.out, a.name), tpl, a.bad, a.great, desk, mgr, a.default_loc, vwc=a.vwc)
    print("page ->", out)

if __name__ == "__main__":
    main()
