#!/usr/bin/env python3
"""Rebuild planner/index.html, the standalone "November MTD Planner" page.

It is the MTD section of day-of-week/index.html on its own: same CSS, HTML and
script (from tools/add_mtd_section.py), with the current DATA_BY_LOC copied
from the live page. The "Weekday analysis" button is hidden because the lower
weekday view is not in this copy.

The planner is also published as a claude.ai artifact ("November MTD Planner",
slug 72e83070-a872-4865-bcf5-c41722138880). Claude Code cannot publish
artifacts; attach planner/index.html in a claude.ai chat to update it there.
"""
import os, re, runpy

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(REPO, "planner", "index.html")
src = open(os.path.join(REPO, "tools", "add_mtd_section.py")).read()
ns = {"__file__": os.path.join(REPO, "tools", "add_mtd_section.py")}
exec(src[: src.index("p = sys.argv[1]")], ns)

a = open(P).read()
a = re.sub(r"\n/\* ---- month to date \(MTD\) ---- \*/.*?(?=\n</style>)", "", a, count=1, flags=re.S)
a = a.replace("\n</style>", ns["CSS"] + "</style>", 1)
a, n1 = re.subn(r'<section class="mtd" id="mtd"[^>]*>.*?</section>\n',
                lambda _: ns["HTML"].replace('<section class="mtd" id="mtd">', '<section class="mtd" id="mtd" style="border-bottom:0">') + "\n",
                a, count=1, flags=re.S)
a, n2 = re.subn(r"\n<script>\n/\* ---- month to date section.*?</script>\n", lambda _: ns["JS"], a, count=1, flags=re.S)
live = open(os.path.join(REPO, "day-of-week", "index.html")).read()
d = re.search(r"const DATA_BY_LOC = .*?;\n", live).group(0)
a, n3 = re.subn(r"const DATA_BY_LOC = .*?;\n", lambda _: d, a, count=1)
if ".tile [data-open]{display:none}" not in a:
    a = a.replace("</style>", ".tile [data-open]{display:none}</style>", 1)
assert (n1, n2, n3) == (1, 1, 1), (n1, n2, n3)
open(P, "w").write(a)
print("planner/index.html rebuilt")
