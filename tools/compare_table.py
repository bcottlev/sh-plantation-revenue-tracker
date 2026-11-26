#!/usr/bin/env python3
"""Print "[Month] 1-[latest day] compared with the same days in past months".

Usage: python3 tools/compare_table.py [--through D] [--months 3]

Each store vs the prior three months over the same calendar days, sorted by
this month's revenue (highest first), then Total system and Palm Beach County
(Wellington, Lake Worth, West Palm Beach, Boynton Beach, Boca Raton) rows.
Markdown table, ready to paste in chat. Bryan wants this with every data update.
"""
import csv, os, re, sys, collections, datetime as D

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PBC = ("Wellington", "Lake Worth", "West Palm Beach", "Boynton Beach", "Boca Raton")

def main(argv):
    nmon = int(argv[argv.index("--months") + 1]) if "--months" in argv else 3
    rows = list(csv.DictReader(open(os.path.join(REPO, "data", "mytime.csv"), encoding="utf-8-sig")))
    c = collections.defaultdict(float); last = None
    for r in rows:
        d = D.datetime.strptime(r["Date"][:10].split(" ")[0], "%m/%d/%Y").date()
        last = d if last is None or d > last else last
        c[(re.split(r" \d", r["Location"])[0], d.year, d.month, d.day)] += float(r["Net Revenue"] or 0)
    thru = int(argv[argv.index("--through") + 1]) if "--through" in argv else last.day
    months = [(last.year, last.month)]
    for _ in range(nmon):
        y, m = months[-1]; months.append((y - 1, 12) if m == 1 else (y, m - 1))
    stores = sorted({k[0] for k in c})
    tot = lambda ls, ym: sum(v for (s, y, m, d), v in c.items() if s in ls and (y, m) == ym and d <= thru)
    cur = months[0]; mn = lambda ym: D.date(ym[0], ym[1], 1).strftime("%b")
    print(f"**{D.date(*cur, 1):%B} 1–{thru} compared with the same days in past months**\n")
    print("| Store | " + " | ".join(mn(ym) for ym in months) + " |")
    print("|---|" + "---|" * len(months))
    def row(name, ls, bold=False):
        v = [tot(ls, ym) for ym in months]
        cells = [f"${v[0]:,.0f}"] + [f"${x:,.0f} ({(v[0]/x-1)*100:+.0f}%)".replace("-", "−") if x else "—" for x in v[1:]]
        n = f"**{name}**" if bold else name
        if bold: cells[0] = f"**{cells[0]}**"
        print(f"| {n} | " + " | ".join(cells) + " |")
    for s in sorted(stores, key=lambda s: -tot([s], cur)):
        if tot([s], cur): row(s, [s])
    row("Total system", stores, True)
    pbc = [s for s in stores if s.startswith(PBC)]
    row("Palm Beach County", pbc, True)
    gone = [p for p in PBC if not any(s.startswith(p) for s in pbc)]
    if gone: print(f"\nPalm Beach County row covers {len(pbc)} stores; not in the exports: {', '.join(gone)}.")

if __name__ == "__main__":
    main(sys.argv[1:])
