#!/usr/bin/env python3
"""Create next month's tracker from the most recent one.

Usage: new_month.py REPO_DIR YYYY-MM TARGET_TOTAL

Copies the latest existing <month>/index.html, swaps month names, day counts and
date prefixes, clears dailyRevenue, and sets targetTotal. Prints the new path.
"""
import sys, os, re, calendar, datetime, glob

STORES = {"plantation": ("Plantation", ""), "pbg-east": ("PBG East", "stores/pbg-east/"),
          "pbg-northlake": ("PBG Northlake", "stores/pbg-northlake/"), "cooper-city": ("Cooper City", "stores/cooper-city/")}
args = [a for a in sys.argv[1:] if not a.startswith("--")]
compare = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--compare=")), None)   # --compare=YYYY-MM
repo, ym, target = args[0], args[1], args[2]
store = args[3] if len(args) > 3 else "plantation"
store_name, store_dir = STORES[store]
y, m = map(int, ym.split('-'))
new_name = datetime.date(y, m, 1).strftime('%B')
new_days = calendar.monthrange(y, m)[1]

# find the most recent existing month tracker to use as template
cands = []
search = [os.path.join(repo, store_dir, '*', 'index.html')]
if store_dir: search.append(os.path.join(repo, '*', 'index.html'))   # fall back to Plantation's as the template
for p in [f for pat in search for f in glob.glob(pat)]:
    name = os.path.basename(os.path.dirname(p)).capitalize()
    try:
        mo = list(calendar.month_name).index(name)
        own = store_dir == "" or p.startswith(os.path.join(repo, store_dir))
        if re.search(r"const dailyRevenue = \{", open(p).read()): cands.append((own, mo, p, name))
    except ValueError:
        pass
if not cands:
    print("no month tracker with a dailyRevenue block found to use as a template"); sys.exit(1)
own, old_mo, src, old_name = max(cands)
old_days = calendar.monthrange(y if old_mo <= m else y - 1, old_mo)[1]
old_prefix = f"{y if old_mo <= m else y-1}-{old_mo:02d}"

s = open(src).read()
s = re.sub(r"const dailyRevenue = \{\n.*?\n(\s*)\};", r"const dailyRevenue = {\n\1};", s, flags=re.S)
s = re.sub(r"const targetTotal = [\d.]+;", f"const targetTotal = {float(target):.0f};", s)
s = s.replace(f"daysIn{old_name}", f"daysIn{new_name}")
s = re.sub(rf"\b{old_name}\s+{old_days}\b", f"{new_name} {new_days}", s)      # "August 31" -> "September 30"
s = re.sub(rf"\b{old_name}\s+31\b", f"{new_name} {new_days}", s)               # catches stale copy errors
s = re.sub(rf"const daysIn{new_name} = \d+;", f"const daysIn{new_name} = {new_days};", s)
s = s.replace(old_prefix, ym)
# prior-month references: the template's "prior" was the month before it; now the template month is the prior
prior_prefix = f"{y if old_mo <= m else y-1}-{old_mo:02d}"
s = re.sub(r"[ \t]*const compareMonth = '[^']*';[^\n]*\n", "", s)   # never inherit a comparison override
if compare:                                                          # --compare=YYYY-MM: compare against that month instead of the prior one
    prior_prefix = compare
    import calendar
    cmp_name = calendar.month_name[int(compare.split("-")[1])]
else:
    cmp_name = old_name
tot_path = os.path.join(repo, store_dir, "month_totals.json") if os.path.exists(os.path.join(repo, store_dir, "month_totals.json")) else os.path.join(repo, "month_totals.json")
if os.path.exists(tot_path):
    import json
    tots = json.load(open(tot_path)); prev = tots.get(prior_prefix)
    if prev:
        s = re.sub(r"const priorTotal = [\d.]+;[^\n]*", (f"const compareMonth = '{compare}';   // comparison month override\n        " if compare else "") + f"const priorTotal = {prev['total']};   // {cmp_name} final (MyTime)", s)
    else:
        print(f"warning: {prior_prefix} not in {tot_path} — run reconcile_month.py first; priorTotal left as-is", file=sys.stderr)
    if True:
        s = re.sub(r'(<span class="label">)\w+( Revenue \(Final\)</span>)', rf"\g<1>{cmp_name}\2", s)
        s = re.sub(r"Pace to match \w+", f"Pace to match {cmp_name}", s)
        s = re.sub(r"matches \w{3}<", f"matches {cmp_name[:3]}<", s)
s = s.replace(old_name, new_name).replace(old_name.lower(), new_name.lower())
# the global rename above also renamed the comparison-month labels when they named the template month: put them back
if cmp_name == old_name:
    s = re.sub(r'(<span class="label">)\w+( Revenue \(Final\)</span>)', rf"\g<1>{cmp_name}\2", s)
    s = re.sub(r"Pace to match \w+", f"Pace to match {cmp_name}", s)
    s = re.sub(r"// \w+ final \(MyTime\)", f"// {cmp_name} final (MyTime)", s)

# a template borrowed from another store starts with no history and no prior-month comparison
if not own:
    s = re.sub(r"const dailyRevenue = \{.*?\n(\s*)\};", r"const dailyRevenue = {\n\1};", s, flags=re.S)
    s = re.sub(r"const priorTotal = [\d.]+;[^\n]*", "const priorTotal = 0;   // no prior month yet", s)
    s = s.replace("Plantation", store_name)
dst_dir = os.path.join(repo, store_dir, new_name.lower()); os.makedirs(dst_dir, exist_ok=True)
dst = os.path.join(dst_dir, 'index.html')
if os.path.exists(dst):
    print(f"{dst} already exists; not overwriting"); sys.exit(2)
open(dst, 'w').write(s)
print(dst)
