#!/usr/bin/env python3
"""Insert (or replace) the "Store health" section on the day-of-week page.

Usage: python3 tools/add_health_section.py day-of-week/index.html [data/mytime.csv]

Monthly figures per store come from data/mytime.csv (ticket level) and are embedded as
HEALTH in the section's own script, so re-running after each data refresh updates them.
The section sits right after the month-to-date section and has two parts:
  - Membership health: members billed on the 1st by month, and new membership sales.
  - Store scorecard: floor revenue per day, service visits per day, average service
    ticket, discount rate and members, each with a 7-month trend.
It also hides the weekday view's "By month" fold, which the scorecard replaces.
Idempotent: removes any earlier copy first.
"""
import csv, json, os, re, sys, calendar, collections, datetime as D

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOFLOOR = {"Cooper City"}          # presale: membership dues only, no services yet
NMONTHS = 7

def loc_name(s):
    return re.split(r" \d", s)[0].strip()

def f(v):
    try: return float(v or 0)
    except ValueError: return 0.0

def build(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    A = collections.defaultdict(lambda: collections.defaultdict(float))
    daynet = collections.defaultdict(float)
    last = D.date(2000, 1, 1)
    for x in rows:
        d = D.datetime.strptime(x["Date"][:10].split(" ")[0], "%m/%d/%Y").date()
        s, k = loc_name(x["Location"]), None
        last = max(last, d)
        a = A[(s, d.year, d.month)]
        svc, mem = f(x["Services"]), f(x["Memberships"])
        a["svc"] += svc; a["svcn"] += svc + f(x["Services Discount"]); a["disc"] += -f(x["Discounts"])
        if svc > 0: a["tix"] += 1
        if d.day == 1:
            if mem > 0: a["mem1"] += 1; a["mem1d"] += mem
        else:
            daynet[(s, d)] += f(x["Net Revenue"])
            if svc > 0: a["vtix"] += 1
            if mem > 0: a["memx"] += 1
    for (s, d), v in daynet.items():
        if v > 0:
            a = A[(s, d.year, d.month)]; a["fnet"] += v; a["fdays"] += 1
    y, cm = last.year, last.month
    months = []
    for i in range(NMONTHS - 1, -1, -1):
        mm, yy = cm - i, y
        while mm < 1: mm += 12; yy -= 1
        months.append((yy, mm))
    stores = sorted({k[0] for k in A})
    out = {}
    for s in stores:
        o = {}
        for (yy, mm) in months:
            a = A.get((s, yy, mm))
            if not a: continue
            span = (last.day if (yy, mm) == (y, cm) else calendar.monthrange(yy, mm)[1]) - 1
            o[f"{yy}-{mm:02d}"] = {
                "floor": round(a["fnet"] / a["fdays"]) if a["fdays"] else None,
                "vis": round(a["vtix"] / a["fdays"], 1) if a["fdays"] else None,
                "avgt": round(a["svcn"] / a["tix"]) if a["tix"] else None,
                "disc": round(a["disc"] / a["svc"] * 100, 1) if a["svc"] else None,
                "mem": int(a["mem1"]) or None, "memd": round(a["mem1d"]),
                "newpm": round(a["memx"] / span * 30) if span > 0 else None,
                "days": int(a["fdays"]),
            }
        if o: out[s] = o
    return {"months": [f"{yy}-{mm:02d}" for yy, mm in months], "thru": last.isoformat(), "nofloor": sorted(NOFLOOR), "stores": out}

CSS = r'''
/* ---- store health ---- */
.hl{margin:0 0 34px;padding-bottom:26px;border-bottom:2px solid var(--daisy)}
body.dark .hl{border-bottom-color:var(--line)}
.hl h2.hl-h{font-family:Fraunces,"Cooper Light",Georgia,serif;font-weight:300;font-variation-settings:"SOFT" 100,"opsz" 96;font-size:clamp(26px,5.4vw,38px);line-height:1.08;margin:0 0 6px;color:var(--shadow)}
body.dark .hl h2.hl-h{color:var(--ink)}
.hl-q{font-weight:700;font-size:15px;color:var(--shadow);margin:20px 0 4px}body.dark .hl-q{color:var(--ink)}
.hl-note{font-size:12.5px;color:var(--mute);margin:6px 0 0}
.hl-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,250px),1fr));gap:10px;margin-top:10px}
.hl-card{background:var(--skye-8);border-radius:12px;padding:12px 14px 10px;font-variant-numeric:tabular-nums}
.hl-card .t{display:flex;justify-content:space-between;align-items:baseline;gap:8px}
.hl-card .n{font-weight:700;font-size:15px;color:var(--shadow)}body.dark .hl-card .n{color:var(--ink)}
.hl-chip{font-size:11.5px;font-weight:700;padding:1px 8px;border-radius:10px;white-space:nowrap}
.hl-chip.dn{background:var(--bad-soft);color:var(--bad)}.hl-chip.up{background:var(--great-soft);color:var(--great)}.hl-chip.fl{background:var(--skye-20);color:var(--ink-70)}
.hl-card .big{font-size:26px;font-weight:700;color:var(--shadow);margin:4px 0 0;line-height:1.1}body.dark .hl-card .big{color:var(--ink)}
.hl-card .big small{font-size:13px;font-weight:500;color:var(--mute);margin-left:6px}
.hl-card .ln{font-size:13px;color:var(--ink-70);margin-top:2px}
.hl-card .ln b{color:var(--ink);font-weight:600}
.hl-spark{display:block;width:100%;height:46px;margin:8px 0 2px}
.hl-ax{display:flex;justify-content:space-between;font-size:10.5px;color:var(--mute)}
.hl .up{color:var(--great)}.hl .down{color:var(--bad)}
.hl-wrap{overflow-x:auto;margin-top:10px;-webkit-overflow-scrolling:touch}
.hl-t{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;min-width:640px}
.hl-t th{font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--mute);text-align:right;padding:0 0 8px 10px;border-bottom:1.5px solid var(--line);white-space:nowrap;vertical-align:bottom}
.hl-t th small{display:block;font-weight:500;letter-spacing:0;text-transform:none;font-size:11px}
.hl-t th:first-child,.hl-t td:first-child{text-align:left;padding-left:0}
.hl-t td{padding:8px 0 8px 10px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap;vertical-align:middle}
.hl-t td:first-child{font-weight:700;color:var(--shadow);font-size:14.5px}body.dark .hl-t td:first-child{color:var(--ink)}
.hl-t tr.sys td{border-top:2px solid var(--shadow);font-weight:700}body.dark .hl-t tr.sys td{border-top-color:#5A5955}
.hl-c{display:inline-grid;grid-template-columns:auto 56px;column-gap:8px;align-items:center;justify-items:end}
.hl-c b{font-size:14.5px;color:var(--ink);font-weight:600}
.hl-c em{font-style:normal;font-size:11.5px;font-weight:600;grid-column:1}
.hl-c svg{grid-row:1/span 2;grid-column:2;width:56px;height:22px}
@media (max-width:560px){.hl-card .big{font-size:22px}}
/* ---- section rhythm: every top-level fold row has the same height, gap and divider ---- */
body .mtd,body .hl{margin:0;padding:0;border-bottom:0}
body .mtd>.fold,body .fold.big,body .days>.fold,body .periods>.fold{margin:0;padding:14px 0}
body .periods,body .days,body .periods:has(> .fold[aria-expanded="false"]),body .days:has(> .fold[aria-expanded="false"]){margin-top:0}
body .mtd>.fold+.fbody:not(.closed),body .fold.big+.fbody:not(.closed),body .days>.fold+.fbody:not(.closed),body .periods>.fold+.fbody:not(.closed){padding:6px 0 28px}
body .mtd-tiles{margin-bottom:12px}
body .sect#weekday header{margin-top:6px}
@media (max-width:560px){body .mtd>.fold,body .fold.big,body .days>.fold,body .periods>.fold{font-size:10.5px;letter-spacing:.07em}}
/* crisp controls: label beside its pills, small pills, tight panels */
body .controls{padding:10px 12px 2px;margin:10px 0 14px;border-radius:10px}
body .ctlrow{column-gap:22px;row-gap:0}body .ctlrow .ctl:last-child{margin-left:0}
body .ctl{display:flex;align-items:center;gap:10px;margin-bottom:8px}
body .ctl>.eyebrow{margin:0;font-size:10px;letter-spacing:.14em;white-space:nowrap}
body .ctl>.seg{flex:1 1 auto;min-width:0}
body .seg{gap:4px}
body .seg button,body .locctl .seg button{font-size:12.5px;padding:4px 10px;border-width:1px}
body .locctl{margin:8px 0 0}body .locctl>.eyebrow{display:none}
body #weekday header .eyebrow{margin-bottom:2px}
body #weekday header h1{font-size:clamp(32px,6vw,42px);margin:0 0 2px}
body #weekday header .compare{margin:0 0 4px}
body .mtd-kpis{gap:8px;margin:0 0 6px}
body .mtd-kpi{padding:7px 12px 8px;border-top-width:2px;border-radius:10px}
body .mtd-kpi>span{font-size:10px;letter-spacing:.12em;margin-bottom:1px}body .mtd-kpi em span{display:inline;font-size:inherit;letter-spacing:0;text-transform:none}
body .mtd-kpi b{font-size:18px;line-height:1.2}
body .mtd-kpi em{font-size:12px;margin-left:6px}
@media (max-width:560px){body .ctl{display:block}body .ctl>.eyebrow{margin-bottom:5px}}
'''

HTML = r'''<section class="hl" id="health">
  <p class="eyebrow fold big" id="hl-eyebrow" role="button" tabindex="0" aria-controls="hl-body" aria-expanded="true" data-open="1"></p>
  <div id="hl-body" class="fbody">
  <h2 class="hl-h" id="hl-head"></h2>
  <p class="range" id="hl-sub"></p>
  <p class="hl-q">Membership health</p>
  <p class="hl-note" id="hl-mnote"></p>
  <div class="hl-cards" id="hl-cards"></div>
  <p class="eyebrow fold" role="button" tabindex="0" aria-controls="hl-score" aria-expanded="false" id="hl-ft">Store scorecard · floor revenue, visits, ticket, discounts, members by month</p>
  <div id="hl-score" class="fbody">
    <div class="hl-wrap"><table class="hl-t" id="hl-table"></table></div>
    <p class="hl-note" id="hl-snote"></p>
  </div>
  </div>
</section>
'''

JS = r'''
<script>
/* ---- store health section: monthly figures built by tools/add_health_section.py ---- */
(function(){
  const H = __HEALTH__;
  const MN = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  const M = H.months, CURK = M[M.length-1], thru = new Date(H.thru + "T12:00"), mlab = k => MN[+k.slice(5)-1];
  const fmt = n => "$" + Math.round(n).toLocaleString("en-US");
  const S = Object.keys(H.stores);
  const series = (s, key) => M.map(k => (H.stores[s][k] || {})[key] ?? null);
  const pctc = (a, b) => a != null && b ? Math.round((a / b - 1) * 100) : null;
  const sgn = v => (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v);
  function spark(vals, w, h, opt){                          // bars for each month; current month in Skye, earlier in gray
    const v = vals.map(x => x == null ? null : x), have = v.filter(x => x != null); if (!have.length) return "";
    const lo = opt && opt.zero ? 0 : Math.min(...have) * .85, hi = Math.max(...have) || 1, n = v.length, bw = w / n;
    return `<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true">` + v.map((x, i) => x == null ? "" :
      `<rect x="${(i*bw + bw*.14).toFixed(1)}" width="${(bw*.72).toFixed(1)}" y="${(h - Math.max(1.5, (x - lo) / (hi - lo || 1) * (h - 2))).toFixed(1)}" height="${Math.max(1.5, (x - lo) / (hi - lo || 1) * (h - 2)).toFixed(1)}" rx="1.5" fill="${i === n-1 ? "var(--skye)" : "var(--skye-45)"}"/>`).join("") + `</svg>`;
  }
  // ---------- membership cards ----------
  const k3 = M[M.length-4];
  const cards = S.map(s => { const mem = series(s, "mem"), nw = series(s, "newpm"), cur = mem[mem.length-1], ago = (H.stores[s][k3] || {}).mem;
    const peak = Math.max(...mem.filter(x => x != null)), ch = ago ? (cur - ago) / ago : null;
    const nwAvg = (() => { const p = nw.slice(-4, -1).filter(x => x != null); return p.length ? p.reduce((a,b) => a+b, 0) / p.length : null; })();
    return {s, mem, nw, cur, ago, peak, ch, nwCur: nw[nw.length-1], nwAvg}; }).filter(c => c.cur != null)
    .sort((a, b) => (a.ch ?? 9) - (b.ch ?? 9));
  const shrinking = cards.filter(c => c.ch != null && c.ch <= -0.05);
  document.getElementById("hl-cards").innerHTML = cards.map(c => {
    const chip = c.ch == null ? ["fl", "new"] : c.ch <= -0.05 ? ["dn", "Shrinking"] : c.ch >= 0.05 ? ["up", "Growing"] : ["fl", "Steady"];
    const d3 = c.ago ? c.cur - c.ago : null, fromPeak = c.peak > c.cur ? c.cur - c.peak : 0;
    const nwc = c.nwAvg ? pctc(c.nwCur, c.nwAvg) : null;
    return `<div class="hl-card"><div class="t"><span class="n">${c.s}</span><span class="hl-chip ${chip[0]}">${chip[1]}</span></div>
      <div class="big">${c.cur}<small>members billed ${mlab(CURK)} 1</small></div>
      <div class="ln">${d3 == null ? "" : `<b class="${d3 < 0 ? "down" : d3 > 0 ? "up" : ""}">${sgn(d3)}</b> since ${mlab(k3)} 1`}${fromPeak < 0 ? ` · peak ${c.peak}` : c.ago ? " · at its peak" : ""}</div>
      ${spark(c.mem, 210, 46)}<div class="hl-ax"><span>${mlab(M[0])}</span><span>${mlab(CURK)}</span></div>
      <div class="ln">New sales: <b>${c.nwCur ?? "—"}</b> per 30 days${nwc == null ? "" : ` <span class="${nwc < 0 ? "down" : "up"}">${nwc > 0 ? "+" : ""}${nwc}%</span> vs prior 3 months`}</div>
      ${c.s === "PBG East" ? `<div class="hl-note">Also bills many members on their sign-up date, so the 1st shows only part of its base and "new sales" includes those renewals.</div>` : ""}</div>`; }).join("");
  document.getElementById("hl-mnote").textContent = `Members = membership charges billed on the 1st of each month. New sales = membership charges on other days, scaled to 30 days (${mlab(CURK)} so far: 1st–${thru.getDate()}). Sorted by the change since ${mlab(k3)}, worst first. Shrinking or growing = 5% or more.`;
  // ---------- scorecard ----------
  const COLS = [["floor","Floor $/day","excl. the 1st",fmt,1],["vis","Visits/day","service tickets",v => v.toFixed(1),1],["avgt","Avg ticket","net services",fmt,1],["disc","Discounts","% of services",v => v.toFixed(1) + "%",-1],["mem","Members","billed on the 1st",v => v,1]];
  const FS = S.filter(s => !H.nofloor.includes(s));
  const prevK = M[M.length-2];
  function cell(vals, col){ const cur = vals[vals.length-1], pv = vals[vals.length-2];
    if (cur == null) return `<td>—</td>`;
    let ch = "";
    if (pv != null) { const dv = col[0] === "disc" ? +(cur - pv).toFixed(1) : pctc(cur, pv); const good = dv * col[4] > 0;
      ch = dv === 0 ? `<em>flat</em>` : `<em class="${good ? "up" : "down"}">${dv > 0 ? "▲" : "▼"} ${Math.abs(dv)}${col[0] === "disc" ? " pts" : "%"}</em>`; }
    return `<td><span class="hl-c"><b>${col[3](cur)}</b>${ch}${spark(vals, 56, 22)}</span></td>`; }
  const sys = {}; M.forEach(k => { const rs = FS.map(s => H.stores[s][k]).filter(r => r && r.days);
    sys[k] = rs.length ? {floor: rs.reduce((a,r) => a + r.floor, 0), vis: +rs.reduce((a,r) => a + r.vis, 0).toFixed(1), mem: rs.reduce((a,r) => a + (r.mem || 0), 0)} : {}; });
  // system avg ticket and discount: weight each store by its visits
  M.forEach(k => { let w = 0, at = 0, dc = 0; FS.forEach(s => { const r = H.stores[s][k]; if (!r || !r.vis) return; const x = r.vis * r.days; w += x; at += r.avgt * x; dc += r.disc * x; }); if (w) { sys[k].avgt = Math.round(at / w); sys[k].disc = +(dc / w).toFixed(1); } });
  const rows = FS.map(s => ({s, v: Object.fromEntries(COLS.map(c => [c[0], series(s, c[0])]))})).sort((a, b) => (b.v.floor.at(-1) || 0) - (a.v.floor.at(-1) || 0));
  document.getElementById("hl-table").innerHTML = `<thead><tr><th>Store</th>${COLS.map(c => `<th>${c[1]}<small>${c[2]}</small></th>`).join("")}</tr></thead><tbody>` +
    rows.map(r => `<tr><td>${r.s}</td>${COLS.map(c => cell(r.v[c[0]], c)).join("")}</tr>`).join("") +
    `<tr class="sys"><td>System (${FS.length})</td>${COLS.map(c => cell(M.map(k => sys[k][c[0]] ?? null), c)).join("")}</tr></tbody>`;
  document.getElementById("hl-snote").textContent = `${mlab(CURK)} so far (1st–${thru.getDate()}) vs all of ${mlab(prevK)}; bars are ${mlab(M[0])}–${mlab(CURK)}, ${mlab(CURK)} in blue. Floor $/day = net revenue on days the store traded, leaving out the 1st's membership billing. Visits/day = tickets with a service. Avg ticket = services after service discounts, per service ticket (membership prepaids not taken off, or member visits would count as $0). Discounts: down is good. System floor and visits are sums; ticket and discounts are visit-weighted. Cooper City is left out until it opens.`;
  // ---------- headline ----------
  const best = rows.filter(r => r.v.floor.at(-1) != null && r.v.floor.at(-1) >= Math.max(...r.v.floor.slice(0, -1).filter(x => x != null))).map(r => r.s);
  document.getElementById("hl-eyebrow").textContent = `Store health · ${mlab(M[0])}–${mlab(CURK)} ${thru.getFullYear()} · by month`;
  document.getElementById("hl-head").textContent = shrinking.length ? `${(n => n.length > 1 ? n.slice(0, -1).join(", ") + " and " + n.at(-1) : n[0])(shrinking.map(c => c.s))} ${shrinking.length > 1 ? "are" : "is"} losing members` : "Membership bases are holding";
  const sf = sys[CURK].floor, sp = sys[prevK].floor;
  document.getElementById("hl-sub").innerHTML = `System floor revenue ${fmt(sf)}/day in ${mlab(CURK)} <span class="${sf >= sp ? "up" : "down"}">${sf >= sp ? "+" : ""}${pctc(sf, sp)}%</span> vs ${mlab(prevK)}${best.length ? ` · best month in this view for ${best.join(", ")}` : ""}`;
})();
</script>
'''

def main(argv):
    page = argv[0]
    data = build(argv[1] if len(argv) > 1 else os.path.join(REPO, "data", "mytime.csv"))
    s = open(page).read()
    s = re.sub(r'\n/\* ---- store health ---- \*/.*?(?=\n</style>)', '', s, count=1, flags=re.S)
    s = re.sub(r'\n*<section class="hl" id="health">.*?</section>\n', '\n', s, count=1, flags=re.S)
    s = re.sub(r'\n+<script>\n/\* ---- store health section.*?</script>\n', '\n', s, count=1, flags=re.S)
    s = s.replace('\n</style>', CSS + '.periods:has(#periods-months){display:none}\n</style>', 1)
    anchor = '<div class="sect" id="weekday">'           # weekday analysis block (collapsible)
    if anchor not in s: anchor = '<header>\n  <p class="eyebrow" id="latestline">'
    assert anchor in s, "anchor missing"
    s = s.replace(anchor, HTML + '\n' + anchor, 1)
    assert s.count('</body>') == 1
    s = s.replace('</body>', JS.replace("__HEALTH__", json.dumps(data, separators=(",", ":"))) + '</body>', 1)
    open(page, "w").write(s)
    print("health: months", data["months"][0], "to", data["months"][-1], "· stores", len(data["stores"]))

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
