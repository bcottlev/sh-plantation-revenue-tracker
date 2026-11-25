"""Insert (or replace) the month-to-date section at the top of the day-of-week page.
Usage: python3 mtd_module.py path/to/day-of-week/index.html
The section reads DATA_BY_LOC from the page itself, so it updates whenever the daily data does.
"""
import sys, re

CSS = r'''
/* ---- month to date (MTD) ---- */
.mtd{margin:0 0 34px;padding-bottom:26px;border-bottom:2px solid var(--daisy)}
.mtd h2.mtd-h{font-family:Fraunces,"Cooper Light",Georgia,serif;font-weight:300;font-variation-settings:"SOFT" 100,"opsz" 96;font-size:clamp(28px,6vw,42px);line-height:1.05;margin:0 0 6px;color:var(--shadow)}
body.dark .mtd h2.mtd-h{color:var(--ink)}
.mtd .controls{margin:14px 0 14px}
.mtd-kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:4px 0 4px}
.mtd-kpi{background:var(--skye-8);border-radius:12px;padding:12px 14px;border-top:3px solid var(--skye)}
.mtd-kpi span{display:block;font-size:11px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--mute)}
.mtd-kpi b{display:block;font-size:clamp(20px,4vw,26px);font-weight:700;color:var(--shadow);font-variant-numeric:tabular-nums;white-space:nowrap}
body.dark .mtd-kpi b{color:var(--ink)}
.mtd-kpi em{font-style:normal;font-size:13px;font-weight:600;color:var(--ink-70)}
.mtd .up{color:var(--great)}.mtd .down{color:var(--bad)}
.mtd-card{background:var(--skye-8);border-radius:12px;padding:14px 16px 10px;margin-top:12px}
.mtd-card header{display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap;align-items:baseline}
.mtd-card header strong{font-size:14px;color:var(--shadow)}body.dark .mtd-card header strong{color:var(--ink)}
.mtd-leg i.fut{background:var(--line);border:1px dashed var(--mute)}
.mtd-leg{font-size:12.5px;color:var(--ink-70);font-weight:500}.mtd-leg i{display:inline-block;width:12px;height:8px;border-radius:2px;margin:0 5px 0 10px;vertical-align:0}
.mtd-fig{position:relative;height:220px;margin-top:6px}.mtd-fig svg{position:absolute;inset:0;width:100%;height:100%}
.mtd-tip{position:absolute;z-index:6;pointer-events:none;background:var(--white);color:var(--ink);border:1px solid var(--line);border-radius:9px;padding:8px 10px;font-size:12.5px;line-height:1.4;box-shadow:0 4px 14px rgba(28,45,90,.18);white-space:nowrap}
.mtd-tip b{display:block}.mtd-tip i{display:inline-block;width:10px;height:6px;border-radius:2px;margin-right:6px}.mtd-tip .s{color:var(--mute);font-size:11.5px}
.mtd-note{font-size:12.5px;color:var(--mute);margin:6px 0 0}
.mtd .fold{margin-top:16px}
.mtd-t{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;margin-top:8px}
.mtd-t th{font-size:11px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--mute);text-align:right;padding:0 0 8px;border-bottom:1.5px solid var(--line);white-space:nowrap}
.mtd-t th:first-child,.mtd-t td:first-child{text-align:left}
.mtd-t th button{all:unset;cursor:pointer;font:inherit;color:inherit;letter-spacing:inherit;text-transform:inherit}
.mtd-t th button i{font-style:normal;font-size:9px;margin-left:4px;opacity:.45}.mtd-t th.on{color:var(--shadow)}.mtd-t th.on button i{opacity:1;color:var(--skye)}
body.dark .mtd-t th.on{color:var(--ink)}.mtd-t th button:hover{color:var(--skye)}.mtd-t th button:focus-visible{outline:2px solid var(--skye);outline-offset:2px}
.mtd-t td{padding:9px 0;border-bottom:1px solid var(--line);text-align:right;font-size:14.5px;color:var(--ink);white-space:nowrap}
.mtd-t td:first-child{font-weight:700;color:var(--shadow);white-space:normal}body.dark .mtd-t td:first-child{color:var(--ink)}
.mtd-t tbody tr[data-s]{cursor:pointer}.mtd-t tbody tr[data-s]:hover td,.mtd-t tr.sel td{background:var(--skye-8)}
.mtd-t tr.grp td{border-top:2px solid var(--shadow);font-weight:700}
.mtd-t .mtd-bar{display:inline-block;height:7px;border-radius:4px;background:var(--skye);vertical-align:middle;margin-left:6px}
.mtd-t input{width:96px;font:500 15px Barlow,sans-serif;padding:5px 7px;border:1.5px solid var(--line);border-radius:7px;background:var(--white);color:var(--ink);text-align:right}
.mtd-t input.d{width:52px}.mtd-t input:focus-visible{outline:2px solid var(--skye);outline-offset:1px}
.mtd-pill{display:inline-block;padding:2px 9px;border-radius:11px;font-size:12.5px;font-weight:700}
.mtd-pill.ok{background:var(--daisy);color:#1C2D5A}.mtd-pill.no{background:var(--bad-soft);color:var(--bad)}
.mtd-q{font-weight:700;font-size:15px;color:var(--shadow);margin:18px 0 8px}body.dark .mtd-q{color:var(--ink)}
.mtd-row{display:grid;grid-template-columns:150px minmax(0,1fr) 190px;gap:12px;align-items:center;padding:9px 0;border-bottom:1px solid var(--line)}
.mtd-row .nm{font-weight:700;color:var(--shadow);font-size:14.5px}body.dark .mtd-row .nm{color:var(--ink)}
.mtd-row .nm small{display:block;font-weight:500;color:var(--mute);font-size:11.5px}
.mtd-trk{position:relative;height:26px;background:var(--skye-8);border-radius:6px}
.mtd-trk .mt{position:absolute;left:0;top:7px;height:12px;border-radius:3px;background:var(--shadow)}body.dark .mtd-trk .mt{background:#C3CCDD}
.mtd-trk .rg{position:absolute;top:4px;height:18px;border-radius:4px;background:var(--skye-45);opacity:.85}
.mtd-trk .md{position:absolute;top:2px;width:2px;height:22px;background:var(--skye);margin-left:-1px}
.mtd-axis{border-bottom:0;padding:0}.mtd-ax{position:relative;height:16px}.mtd-ax span{position:absolute;transform:translateX(-50%);font-size:11px;color:var(--mute);font-weight:600}
.mtd-trk .tg{position:absolute;top:-3px;width:3px;height:32px;background:var(--daisy);margin-left:-1.5px;border-radius:2px;box-shadow:0 0 0 1px rgba(28,45,90,.35)}
.mtd-row .rt{text-align:right;font-size:13px;color:var(--ink-70);line-height:1.35}
.mtd-row .rt b{color:var(--ink);font-size:14px}
.mtd-st{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11.5px;font-weight:700;margin-left:6px;vertical-align:1px}
.mtd-st.ok{background:var(--great-soft);color:var(--great)}.mtd-st.reach{background:var(--skye-20);color:var(--shadow)}.mtd-st.str{background:rgba(255,231,63,.45);color:#1C2D5A}.mtd-st.risk{background:var(--bad-soft);color:var(--bad)}
body.dark .mtd-st.reach{color:var(--ink)}
.mtd-dsum{font-size:14px;color:var(--ink-70);margin:10px 0 8px}.mtd-dsum b{color:var(--ink)}
.mtd-days{display:grid;grid-template-columns:repeat(auto-fill,minmax(98px,1fr));gap:8px}
.mtd-day{border-radius:10px;padding:9px 10px;background:var(--skye-8);border:1.5px solid transparent;font-variant-numeric:tabular-nums}
.mtd-day .w{font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--mute)}
.mtd-day .v{font-size:18px;font-weight:700;color:var(--shadow);margin-top:2px}body.dark .mtd-day .v{color:var(--ink)}
.mtd-day .x{font-size:11.5px;color:var(--mute)}
.mtd-day.next{border-color:var(--skye);background:var(--white)}
.mtd-day.big{border-color:var(--daisy)}
.mtd-day.closed{opacity:.55}.mtd-day.closed .v{font-size:14px;color:var(--mute)}
.mtd-day.hit{background:var(--great-soft)}.mtd-day.miss{background:var(--bad-soft)}
.mtd-day.hit .v{color:var(--great)}.mtd-day.miss .v{color:var(--bad)}
.mtd-copyrow{display:flex;align-items:center;gap:12px;margin-top:12px;flex-wrap:wrap}
.mtd-copy{font:inherit;font-size:13.5px;font-weight:700;padding:8px 14px;border-radius:999px;border:1.5px solid var(--shadow);background:var(--shadow);color:#fff;cursor:pointer}
body.dark .mtd-copy{background:var(--daisy);border-color:var(--daisy);color:#1C2D5A}
.mtd-copy:focus-visible{outline:2px solid var(--skye);outline-offset:2px}
.mtd-pre{white-space:pre-wrap;background:var(--skye-8);border-radius:8px;padding:10px 12px;font-size:13px;color:var(--ink);margin-top:8px}
@media (max-width:560px){
 .mtd-row{grid-template-columns:minmax(0,1fr);gap:5px}.mtd-row .rt{text-align:left}.mtd-axis .rt,.mtd-axis>div:first-child{display:none}
 .mtd-days{grid-template-columns:repeat(3,minmax(0,1fr))}
 .mtd-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}
 .mtd-t td{font-size:13px}.mtd-t th{font-size:10px;letter-spacing:.08em}.mtd-t .mtd-bar{display:none}
}
'''

HTML = r'''<section class="mtd" id="mtd">
  <p class="eyebrow" id="mtd-eyebrow">Month to date · all scenters</p>
  <h2 class="mtd-h" id="mtd-head"></h2>
  <p class="range" id="mtd-sub"></p>
  <div class="controls">
    <div class="ctlrow">
      <div class="ctl"><p class="eyebrow">Measure</p><div class="seg" id="mtd-meas" role="group" aria-label="MTD measure"></div></div>
      <div class="ctl"><p class="eyebrow">Compare to</p><div class="seg" id="mtd-cmp" role="group" aria-label="Compare month"></div></div>
    </div>
  </div>
  <div class="mtd-kpis" id="mtd-kpis"></div>
  <div class="mtd-card">
    <header><strong id="mtd-ta"></strong><span class="mtd-leg"><i style="background:var(--great)"></i>Ahead<i style="background:var(--bad)"></i>Behind<i class="fut"></i>Days to come</span></header>
    <div class="mtd-fig" id="mtd-fa"><svg id="mtd-sa" role="img" aria-label="Running gap versus comparison month"></svg><div class="mtd-tip" id="mtd-pa" hidden></div></div>
  </div>
  <div class="mtd-card">
    <header><strong id="mtd-tb"></strong><span class="mtd-leg"><i style="background:var(--skye)"></i><span id="mtd-lcur"></span><i style="background:var(--skye-45)"></i><span id="mtd-lcmp"></span><i class="fut"></i>Days to come</span></header>
    <div class="mtd-fig" id="mtd-fb"><svg id="mtd-sb" role="img" aria-label="Daily revenue, this month versus comparison month"></svg><div class="mtd-tip" id="mtd-pb" hidden></div></div>
    <p class="mtd-note">Hover or tap either chart for that day. Tap a store in the table below to chart it.</p>
  </div>
  <p class="eyebrow fold" role="button" tabindex="0" aria-controls="mtd-stores" aria-expanded="false" id="mtd-ft"></p>
  <div id="mtd-stores" class="fbody"></div>
  <p class="eyebrow fold" role="button" tabindex="0" aria-controls="mtd-planbox" aria-expanded="false" id="mtd-fp"></p>
  <div id="mtd-planbox" class="fbody">
    <p class="mtd-q">1 · Will each store make it?</p>
    <div id="mtd-odds"></div>
    <p class="mtd-note" id="mtd-oddsnote"></p>
    <p class="mtd-q">2 · What each store needs, day by day</p>
    <div class="seg" id="mtd-pick" role="group" aria-label="Store for daily targets"></div>
    <p class="mtd-dsum" id="mtd-dsum"></p>
    <div class="mtd-days" id="mtd-days"></div>
    <div class="mtd-copyrow"><button type="button" class="mtd-copy" id="mtd-copy">Copy for Slack</button><span class="mtd-note" id="mtd-copied"></span></div>
    <pre class="mtd-pre" id="mtd-pre" hidden></pre>
  </div>
</section>
'''

JS = r'''
<script>
/* ---- month to date section: built from DATA_BY_LOC on this page ---- */
(function(){
  const STORES = Object.keys(DATA_BY_LOC).filter(s => (DATA_BY_LOC[s] || []).length);
  if (!STORES.length) { document.getElementById("mtd").style.display = "none"; return; }
  const MN = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  const DNS = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
  const HOLI = new Set(["01-01","11-26","12-25"]);           // closed at every scenter (2026)
  const CLOSED_DOW = {"PBG Northlake":[0]};                  // JS getDay(): 0 = Sunday
  const DEF_T = {"Plantation":34000,"PBG East":28500,"PBG Northlake":17000};
  const GROUPS = [["Total system",STORES],["Broward (Plantation + Cooper City)",["Plantation","Cooper City"]],["PBG (East + Northlake)",["PBG East","PBG Northlake"]],["Palm Beach County",["Wellington","Lake Worth","West Palm Beach","Boynton Beach","Boca Raton West"]]]
    .map(([n,l]) => [n, l.filter(s => STORES.includes(s))]).filter(g => g[1].length > 1);
  // day grid: G[store][month] = {net:[31], mem:[31], has:[31]}
  const G = {}; let lastM = 0, lastD = 0;
  STORES.forEach(s => { G[s] = {}; DATA_BY_LOC[s].forEach(r => {
    const m = +r[0].slice(0,2), d = +r[0].slice(3,5);
    const g = G[s][m] || (G[s][m] = {net:Array(31).fill(0), mem:Array(31).fill(0), has:Array(31).fill(false)});
    const net = +r[2] || 0, nm = r[3] == null ? net : +r[3];
    g.net[d-1] += net; g.mem[d-1] += net - nm; g.has[d-1] = true;
    if (m > lastM || (m === lastM && d > lastD)) { lastM = m; lastD = d; }
  }); });
  const CUR = lastM, THRU = lastD, DIM = m => new Date(YEAR, m, 0).getDate();
  const CMPS = [CUR-1, CUR-2, CUR-3].filter(m => m >= 1);
  const MEAS = {total:"Total", mem:"Memberships", add:"Add-ons & other"};
  let st = {m:"total", c:CMPS[0], sel:"Total system", sk:"n", sd:-1};
  const fmt = n => (n < 0 ? "-" : "") + "$" + Math.abs(Math.round(n)).toLocaleString("en-US");
  const kf = v => { const a = Math.abs(v); return (v < 0 ? "-" : "") + "$" + (a >= 1000 ? (a/1000).toFixed(a >= 10000 ? 0 : 1) + "k" : Math.round(a)); };
  const pct = (a,b) => b ? Math.round((a/b - 1) * 100) : null;
  const pc = p => p == null ? "—" : `<span class="${p >= 0 ? "up" : "down"}">${p > 0 ? "+" : ""}${p}%</span>`;
  const val = (s,m,d) => { const g = G[s][m]; if (!g) return 0; const n = g.net[d-1], me = g.mem[d-1]; return st.m === "total" ? n : st.m === "mem" ? me : n - me; };
  const has = (s,m) => !!G[s][m];
  const day = (ls,m,d) => ls.reduce((a,s) => a + val(s,m,d), 0);
  const sum = (ls,m,to) => { let t = 0; for (let d = 1; d <= to; d++) t += day(ls,m,d); return t; };
  const cum = (ls,m,to) => { const o = []; let t = 0; for (let d = 1; d <= to; d++) { t += day(ls,m,d); o.push(t); } return o; };
  const storesOf = n => (GROUPS.find(g => g[0] === n) || [n, [n]])[1];
  const ticks = (lo,hi,n) => { const sp = hi - lo || 1, s0 = sp / n, mg = 10 ** Math.floor(Math.log10(s0)), step = [1,2,2.5,5,10].map(x => x*mg).find(x => x >= s0); const o = []; for (let v = Math.ceil(lo/step)*step; v <= hi + 1e-9; v += step) o.push(v); return o; };
  const ord = n => n + (n % 10 === 1 && n !== 11 ? "st" : n % 10 === 2 && n !== 12 ? "nd" : n % 10 === 3 && n !== 13 ? "rd" : "th");
  let CH = null;
  function seg(id, opts, key){
    const el = document.getElementById(id);
    el.innerHTML = opts.map(([v,l]) => `<button data-v="${v}"${st[key] == v ? ' aria-pressed="true"' : ""}>${l}</button>`).join("");
    el.onclick = e => { const b = e.target.closest("button"); if (!b) return; st[key] = key === "c" ? +b.dataset.v : b.dataset.v; render(); };
  }
  function prep(){
    const ls = storesOf(st.sel), cd = DIM(st.c);
    const nov = cum(ls, CUR, THRU), pri = cum(ls, st.c, cd);
    const dn = [], dp = []; for (let d = 1; d <= 31; d++) { dn.push(d <= THRU ? day(ls, CUR, d) : null); dp.push(d <= cd ? day(ls, st.c, d) : null); }
    CH = {ls, cd, nov, pri, dn, dp, gap: nov.map((v,i) => v - pri[i])};
  }
  const svgA = document.getElementById("mtd-sa"), svgB = document.getElementById("mtd-sb");
  function axis(o, lo, hi, y, pl, W, pr){ for (const v of ticks(lo,hi,4)) o.push(`<line x1="${pl}" x2="${W-pr}" y1="${y(v)}" y2="${y(v)}" stroke="var(--line)"/><text x="${pl-6}" y="${y(v)+4}" text-anchor="end" font-size="11" fill="var(--mute)">${kf(v)}</text>`); }
  function future(o, x, bw, W, pr, pt, H, pb, dim){
    if (THRU >= dim) return; const x0 = x(THRU + 1), x1 = Math.min(x(dim) + bw, W - pr);
    o.push(`<rect x="${x0}" y="${pt}" width="${x1 - x0}" height="${H - pt - pb}" fill="var(--line)" opacity=".45"/>`);
    o.push(`<line x1="${x0}" x2="${x0}" y1="${pt}" y2="${H - pb}" stroke="var(--mute)" stroke-dasharray="3 3"/>`);
    o.push(`<text x="${(x0 + x1) / 2}" y="${H - pb - 6}" text-anchor="middle" font-size="11" font-weight="600" fill="var(--mute)">${dim - THRU} day${dim - THRU > 1 ? "s" : ""} to come</text>`);
  }
  function xlab(o, x, bw, H){ for (const d of [1,8,15,22,29]) o.push(`<text x="${x(d)+bw/2}" y="${H-6}" text-anchor="middle" font-size="11" fill="var(--mute)">${d}</text>`); }
  function drawA(){
    if (!CH) return; const W = svgA.clientWidth, H = svgA.clientHeight; if (!W) return;
    const pl = W < 520 ? 42 : 54, pr = 8, pt = 10, pb = 22, g = CH.gap;
    const mx = Math.max(...g.map(Math.abs), 1) * 1.15, lo = Math.min(...g) < 0 ? -mx : -mx * .15, hi = Math.max(...g) > 0 ? mx : mx * .15;
    const bw = (W - pl - pr) / 31, x = d => pl + (d-1) * bw, y = v => pt + (hi - v) / (hi - lo) * (H - pt - pb);
    const o = []; future(o, x, bw, W, pr, pt, H, pb, DIM(CUR)); axis(o, lo, hi, y, pl, W, pr);
    o.push(`<line x1="${pl}" x2="${W-pr}" y1="${y(0)}" y2="${y(0)}" stroke="var(--shadow)" stroke-width="1.2"/>`);
    g.forEach((v,i) => { const y0 = y(0), y1 = y(v); o.push(`<rect x="${(x(i+1)+bw*.15).toFixed(1)}" width="${(bw*.7).toFixed(1)}" y="${Math.min(y0,y1).toFixed(1)}" height="${Math.max(1,Math.abs(y1-y0)).toFixed(1)}" rx="2" fill="${v >= 0 ? "var(--great)" : "var(--bad)"}"/>`); });
    xlab(o, x, bw, H);
    const L = g[g.length-1]; o.push(`<text x="${Math.min(x(THRU)+bw+4, W-pr-56)}" y="${y(L)+(L >= 0 ? -6 : 14)}" font-size="12" font-weight="700" fill="var(--ink)">${L >= 0 ? "+" : ""}${kf(L)}</text>`);
    o.push(`<rect id="mtd-ha" y="${pt}" height="${H-pt-pb}" width="${bw}" fill="var(--shadow)" opacity="0"/>`);
    svgA.innerHTML = o.join(""); svgA._g = {pl, bw, N: THRU};
  }
  function drawB(){
    if (!CH) return; const W = svgB.clientWidth, H = svgB.clientHeight; if (!W) return;
    const pl = W < 520 ? 42 : 54, pr = 8, pt = 10, pb = 22;
    const all = [...CH.dn, ...CH.dp].filter(v => v != null), rest = [...CH.dn.slice(1), ...CH.dp.slice(1)].filter(v => v != null);
    const d1 = Math.max(CH.dn[0] || 0, CH.dp[0] || 0), rm = Math.max(...rest, 1), clip = d1 > rm * 1.6;
    const hi = (clip ? rm : Math.max(...all, 1)) * 1.12, lo = Math.min(0, ...all);
    const bw = (W - pl - pr) / 31, x = d => pl + (d-1) * bw, y = v => pt + (hi - v) / (hi - lo) * (H - pt - pb), w = bw * .38, cl = v => Math.min(v, hi);
    const o = []; future(o, x, bw, W, pr, pt, H, pb, DIM(CUR)); axis(o, lo, hi, y, pl, W, pr);
    for (let d = 1; d <= 31; d++) { const p = CH.dp[d-1], n = CH.dn[d-1], fut = d > THRU;
      if (p != null) o.push(`<rect x="${(x(d)+bw*.1).toFixed(1)}" width="${w.toFixed(1)}" y="${Math.min(y(0),y(cl(p))).toFixed(1)}" height="${Math.max(1,Math.abs(y(cl(p))-y(0))).toFixed(1)}" rx="1.5" fill="var(--skye-45)"${fut ? ' fill-opacity=".35" stroke="var(--skye-45)" stroke-dasharray="2 2"' : ""}/>`);
      if (n != null) o.push(`<rect x="${(x(d)+bw*.1+w).toFixed(1)}" width="${w.toFixed(1)}" y="${Math.min(y(0),y(cl(n))).toFixed(1)}" height="${Math.max(1,Math.abs(y(cl(n))-y(0))).toFixed(1)}" rx="1.5" fill="var(--skye)"/>`); }
    xlab(o, x, bw, H);
    if (clip) o.push(`<text x="${x(2)+4}" y="${y(hi)+12}" font-size="11" fill="var(--mute)">${W < 520 ? "Day 1 cut off: " + kf(CH.dn[0] || 0) : "Day 1 (membership billing): " + kf(CH.dn[0] || 0) + " vs " + kf(CH.dp[0] || 0) + ", bars cut off"}</text>`);
    o.push(`<rect id="mtd-hb" y="${pt}" height="${H-pt-pb}" width="${bw}" fill="var(--shadow)" opacity="0"/>`);
    svgB.innerHTML = o.join(""); svgB._g = {pl, bw, N: 31};
  }
  const roA = new ResizeObserver(drawA); roA.observe(svgA); const roB = new ResizeObserver(drawB); roB.observe(svgB);
  function tipHtml(d){
    const hn = d <= THRU, hp = d <= CH.cd, wn = DNS[new Date(YEAR, CUR-1, d).getDay()], wp = DNS[new Date(YEAR, st.c-1, d).getDay()];
    let h = `<b>Day ${d}</b>`;
    if (hn && hp) { const g = CH.gap[d-1]; h += `<div class="${g >= 0 ? "up" : "down"}" style="font-weight:700">${g >= 0 ? "Ahead" : "Behind"} ${fmt(Math.abs(g))} MTD (${pc(pct(CH.nov[d-1], CH.pri[d-1]))})</div>`; }
    if (hn) h += `<div><i style="background:var(--skye)"></i>${MN[CUR-1]} ${d} (${wn}): ${fmt(CH.dn[d-1])} that day</div><div class="s">${fmt(CH.nov[d-1])} month to date</div>`;
    if (hp) h += `<div><i style="background:var(--skye-45)"></i>${MN[st.c-1]} ${d} (${wp}): ${fmt(CH.dp[d-1])} that day</div><div class="s">${fmt(CH.pri[d-1])} month to date</div>`;
    return h;
  }
  [["a", svgA], ["b", svgB]].forEach(([k, svg]) => {
    const fig = document.getElementById("mtd-f" + k), tip = document.getElementById("mtd-p" + k);
    const leave = () => { tip.hidden = true; const h = document.getElementById("mtd-h" + k); if (h) h.setAttribute("opacity", "0"); };
    const move = ev => { if (!CH || !svg._g) return; const g = svg._g, r = svg.getBoundingClientRect(); const d = Math.floor((ev.clientX - r.left - g.pl) / g.bw) + 1;
      if (d < 1 || d > g.N || (d > THRU && d > CH.cd)) return leave();
      const h = document.getElementById("mtd-h" + k); h.setAttribute("x", g.pl + (d-1) * g.bw); h.setAttribute("opacity", ".07");
      tip.innerHTML = tipHtml(d); tip.hidden = false;
      const X = g.pl + (d - .5) * g.bw, fw = fig.clientWidth, tw = tip.offsetWidth; let L = X + 14; if (L + tw > fw) L = X - tw - 14; if (L < 0) L = 0;
      tip.style.left = L + "px"; tip.style.top = "2px"; };
    fig.addEventListener("pointermove", move); fig.addEventListener("pointerdown", move); fig.addEventListener("pointerleave", leave);
  });
  function stores(){
    const cs = CMPS;
    const v = ls => [CUR, ...cs].map(m => ls.some(s => has(s, m)) ? sum(ls, m, THRU) : null);
    const key = s => { const a = v([s]); return st.sk === "s" ? s : st.sk === "n" ? a[0] : (pct(a[0], a[+st.sk]) ?? -1e9); };
    const rows = STORES.slice().sort((x,y) => { const a = key(x), b = key(y); return (typeof a === "string" ? a.localeCompare(b) : a - b) * st.sd; });
    const top = Math.max(...STORES.map(s => v([s])[0]), 1);
    const th = (k,l) => `<th class="${st.sk === k ? "on" : ""}" data-k="${k}" aria-sort="${st.sk === k ? (st.sd > 0 ? "ascending" : "descending") : "none"}"><button type="button">${l}<i>${st.sk === k ? (st.sd > 0 ? "▲" : "▼") : "⇅"}</i></button></th>`;
    const tr = (name, ls, cls) => { const a = v(ls); return `<tr class="${cls || ""}${st.sel === name ? " sel" : ""}" data-s="${name}"><td>${name}</td><td>${fmt(a[0])}${ls.length > 1 ? "" : `<span class="mtd-bar" style="width:${Math.max(2, a[0]/top*70)}px"></span>`}</td>${cs.map((m,i) => `<td>${pc(a[i+1] == null ? null : pct(a[0], a[i+1]))}</td>`).join("")}</tr>`; };
    document.getElementById("mtd-stores").innerHTML = `<table class="mtd-t"><thead><tr>${th("s","Store")}${th("n", MN[CUR-1] + " 1–" + THRU)}${cs.map((m,i) => th(String(i+1), "vs " + MN[m-1])).join("")}</tr></thead><tbody>` +
      rows.map(s => tr(s, [s])).join("") + GROUPS.map((g,i) => tr(g[0], g[1], i === 0 ? "grp" : "")).join("") + `</tbody></table>`;
  }
  document.getElementById("mtd-stores").addEventListener("click", e => {
    const h = e.target.closest("th[data-k]"); if (h) { const k = h.dataset.k; if (st.sk === k) st.sd *= -1; else { st.sk = k; st.sd = k === "s" ? 1 : -1; } stores(); return; }
    const r = e.target.closest("tr[data-s]"); if (r) { st.sel = r.dataset.s; render(); }
  });
  // ---------- planner: weekday-aware forecast, odds and daily targets ----------
  const pad = n => String(n).padStart(2,"0");
  const mmdd = dt => pad(dt.getMonth()+1) + "-" + pad(dt.getDate());
  const wdIdx = dt => (dt.getDay() + 6) % 7;                 // 0 = Mon … 6 = Sun, as in the data
  const thanks = m => { if (m !== 11) return null; const f = new Date(YEAR, 10, 1); const first = 1 + ((4 - f.getDay() + 7) % 7); return first + 21; };
  function kind(s, dt){                                     // "closed" | "sat" (holiday eve, plays like a Saturday) | "normal"
    const k = mmdd(dt), tg = thanks(dt.getMonth()+1);
    if (HOLI.has(k) || (tg && dt.getMonth() === 10 && dt.getDate() === tg)) return "closed";
    if ((CLOSED_DOW[s] || []).includes(dt.getDay())) return "closed";
    if (tg && dt.getMonth() === 10 && dt.getDate() === tg - 1) return "sat";
    if (k === "12-24" || k === "12-31") return "sat";
    return "normal";
  }
  function wstats(s){                                       // last 6 weeks, per weekday: mean, p25, p75 (billing days and the 1st excluded)
    const end = new Date(YEAR, CUR-1, THRU), by = Array.from({length:7}, () => []);
    DATA_BY_LOC[s].forEach(r => { const dt = new Date(YEAR, +r[0].slice(0,2)-1, +r[0].slice(3,5)), age = (end - dt) / 864e5;
      if (age >= 0 && age < 42 && r[4] !== 1 && +r[0].slice(3,5) !== 1 && (+r[2] || 0) > 0) by[r[1]].push(+r[2]); });
    return by.map(v => { v.sort((a,b) => a-b); if (!v.length) return {m:0, lo:0, hi:0, n:0}; const q = p => v[Math.min(v.length-1, Math.round(p*(v.length-1)))];
      return {m: v.reduce((a,b) => a+b, 0) / v.length, lo: q(.25), hi: q(.75), n: v.length}; });
  }
  function target(s){ if (DEF_T[s]) return {t: DEF_T[s], src: "bonus target"};
    const g = G[s][CUR-1]; const prev = g ? g.net.reduce((a,b) => a+b, 0) : 0; return {t: Math.round(prev * 1.1 / 100) * 100, src: MN[(CUR+10)%12] + " +10%"}; }
  function model(s){
    const W = wstats(s), dim = DIM(CUR), g = G[s][CUR]; let mtd = 0; if (g) for (let d = 0; d < THRU; d++) mtd += g.net[d];
    const days = []; for (let d = THRU + 1; d <= dim; d++) { const dt = new Date(YEAR, CUR-1, d), k = kind(s, dt), w = k === "sat" ? 5 : wdIdx(dt);
      days.push({d, dt, k, base: k === "closed" ? 0 : W[w].m, lo: k === "closed" ? 0 : W[w].lo, hi: k === "closed" ? 0 : W[w].hi}); }
    const T = target(s), sm = days.reduce((a,x) => a + x.base, 0), lo = mtd + days.reduce((a,x) => a + x.lo, 0), hi = mtd + days.reduce((a,x) => a + x.hi, 0), mid = mtd + sm;
    const gap = T.t - mtd, lift = sm ? gap / sm - 1 : (gap > 0 ? Infinity : -1), k = gap > 0 && sm ? gap / sm : 1;
    days.forEach(x => x.tgt = x.k === "closed" ? 0 : Math.round(x.base * Math.max(k, 1) / 10) * 10);
    // the week behind: actual vs that weekday's normal
    const past = []; for (let d = Math.max(1, THRU - 6); d <= THRU; d++) { const dt = new Date(YEAR, CUR-1, d), w = wdIdx(dt), act = g ? g.net[d-1] : 0, k2 = kind(s, dt);
      if (d === 1) continue; past.push({d, dt, act, base: k2 === "closed" ? 0 : W[k2 === "sat" ? 5 : w].m, k: k2}); }
    const status = lo >= T.t ? ["ok","On track"] : mid >= T.t ? ["reach","Likely"] : hi >= T.t ? ["str","Within reach"] : ["risk","At risk"];
    return {s, mtd, T, lo, mid, hi, gap, lift, days, past, status, open: days.filter(x => x.k !== "closed").length};
  }
  let PICK = null;
  function liftTxt(m){ return m.gap <= 0 ? "target already reached" : m.lift <= 0 ? `a normal week clears it by ${fmt(-m.lift * (m.mid - m.mtd))}` : `needs <b>${Math.round(m.lift*100)}% above</b> a normal week`; }
  function plan(){
    const M = STORES.map(model).sort((a,b) => b.lift - a.lift);
    // every row on the same scale: % of its own target, 60% to 120%, so the targets line up
    const A = .6, B = 1.2; let P;
    document.getElementById("mtd-odds").innerHTML = `<div class="mtd-row mtd-axis"><div></div><div class="mtd-ax">${[.6,.7,.8,.9,1,1.1,1.2].map(v => `<span style="left:${(v-A)/(B-A)*100}%">${Math.round(v*100)}%</span>`).join("")}</div><div class="rt">of target</div></div>` + M.map(m => { P = v => Math.max(0, Math.min(100, (v / m.T.t - A) / (B - A) * 100)); return `<div class="mtd-row"><div class="nm">${m.s}<span class="mtd-st ${m.status[0]}">${m.status[1]}</span><small>target ${fmt(m.T.t)} · ${m.T.src}</small></div>
      <div class="mtd-trk" title="So far ${fmt(m.mtd)} · likely ${fmt(m.lo)}–${fmt(m.hi)} · target ${fmt(m.T.t)}"><span class="rg" style="left:${P(m.lo)}%;width:${Math.max(.6, P(m.hi)-P(m.lo))}%"></span><span class="mt" style="width:${P(m.mtd)}%"></span><span class="md" style="left:${P(m.mid)}%"></span><span class="tg" style="left:${P(m.T.t)}%"></span></div>
      <div class="rt"><b>${fmt(m.lo)}–${fmt(m.hi)}</b> likely<br>${liftTxt(m)}</div></div>`; }).join("");
    document.getElementById("mtd-oddsnote").innerHTML = `Dark bar = revenue so far. Blue band = likely month end from each store's own last 6 weeks, weekday by weekday (middle half of outcomes; line = typical). Yellow tick = target; every row is drawn as a % of its own target, so the ticks line up. ${thanks(CUR) ? "Thanksgiving closed; the day before is planned like a Saturday." : ""} Sorted hardest first.`;
    if (!PICK || !STORES.includes(PICK)) PICK = M[0].s;
    const pk = document.getElementById("mtd-pick");
    pk.innerHTML = M.map(m => `<button data-s="${m.s}"${m.s === PICK ? ' aria-pressed="true"' : ""}>${m.s}</button>`).join("");
    daily(M.find(m => m.s === PICK));
  }
  let LASTTXT = "";
  function daily(m){
    const S = d => DNS[d.dt.getDay()] + " " + (d.dt.getMonth()+1) + "/" + d.d;
    document.getElementById("mtd-dsum").innerHTML = `<b>${m.s}</b>: ${fmt(m.mtd)} so far, target ${fmt(m.T.t)}. ${m.gap > 0 ? `${fmt(m.gap)} to go over ${m.open} open day${m.open === 1 ? "" : "s"}, ${liftTxt(m)}.` : "Target reached; the cards show a normal week."}`;
    const big = Math.max(...m.days.map(x => x.tgt));
    const past = m.past.map(x => { const ok = x.k === "closed" ? null : x.act >= x.base; return `<div class="mtd-day ${x.k === "closed" ? "closed" : ok ? "hit" : "miss"}"><div class="w">${S(x)}</div><div class="v">${x.k === "closed" && !x.act ? "closed" : fmt(x.act)}</div><div class="x">${x.k === "closed" ? "" : "normal " + fmt(x.base)}</div></div>`; }).join("");
    const fut = m.days.map((x,i) => x.k === "closed" ? `<div class="mtd-day closed"><div class="w">${S(x)}</div><div class="v">closed</div><div class="x">${mmdd(x.dt) === "11-" + thanks(11) ? "Thanksgiving" : ""}</div></div>`
      : `<div class="mtd-day${i === m.days.findIndex(y => y.k !== "closed") ? " next" : ""}${x.tgt === big ? " big" : ""}"><div class="w">${S(x)}${x.k === "sat" ? " ★" : ""}</div><div class="v">${fmt(x.tgt)}</div><div class="x">${x.k === "sat" ? "holiday eve" : "normal " + fmt(x.base)}</div></div>`).join("");
    document.getElementById("mtd-days").innerHTML = (past ? `<div class="mtd-day" style="grid-column:1/-1;background:none;padding:0 0 2px"><div class="w">This past week · actual vs a normal day</div></div>` + past : "") +
      `<div class="mtd-day" style="grid-column:1/-1;background:none;padding:8px 0 2px"><div class="w">Targets for the days left</div></div>` + (fut || `<div class="mtd-day closed"><div class="v">month complete</div></div>`);
    const lines = m.days.filter(x => x.k !== "closed").map(x => `${S(x)}: ${fmt(x.tgt)}${x.k === "sat" ? " (holiday eve)" : ""}`);
    LASTTXT = `*${m.s} · ${MN[CUR-1]} targets*\nSo far: ${fmt(m.mtd)} · Target: ${fmt(m.T.t)}${m.gap > 0 ? ` · ${fmt(m.gap)} to go` : " ✅"}\n` + lines.join("\n");
    document.getElementById("mtd-pre").hidden = true; document.getElementById("mtd-copied").textContent = "";
  }
  document.getElementById("mtd-pick").addEventListener("click", e => { const b = e.target.closest("button"); if (!b) return; PICK = b.dataset.s; plan(); });
  document.getElementById("mtd-copy").addEventListener("click", async () => {
    const out = document.getElementById("mtd-copied"), pre = document.getElementById("mtd-pre");
    try { await navigator.clipboard.writeText(LASTTXT); out.textContent = "Copied. Review it before you send it."; pre.hidden = true; }
    catch (e) { pre.textContent = LASTTXT; pre.hidden = false; out.textContent = "Copy didn't work here; select the text below."; }
  });
  function render(){
    seg("mtd-meas", Object.entries(MEAS), "m"); seg("mtd-cmp", CMPS.map(m => [m, MN[m-1]]), "c");
    const n = sum(STORES, CUR, THRU), c = sum(STORES, st.c, THRU), p = pct(n, c);
    document.getElementById("mtd-eyebrow").textContent = `Month to date · ${MN[CUR-1]} 1–${THRU}, ${YEAR} · all scenters`;
    document.getElementById("mtd-head").textContent = p == null ? `${MEAS[st.m]} ${fmt(n)} month to date` : `${MEAS[st.m]} is ${p >= 0 ? "up" : "down"} ${Math.abs(p)}% vs ${MN[st.c-1]} through the ${ord(THRU)}`;
    document.getElementById("mtd-sub").textContent = `${STORES.length} scenters, the 1st to the ${ord(THRU)} of each month. ${st.m === "mem" ? "Memberships bill mostly on the 1st, so they move slowly." : st.m === "add" ? "Add-ons & other move with how busy the stores are." : "Switch the measure to see memberships and add-ons separately."}`;
    document.getElementById("mtd-kpis").innerHTML = [[CUR, n, MN[CUR-1] + " 1–" + THRU, "this month"], ...CMPS.map(m => { const v = sum(STORES, m, THRU); return [m, v, MN[m-1] + " 1–" + THRU, pc(pct(n, v)) + " vs " + MN[m-1]]; })]
      .map(([m,v,l,d]) => `<div class="mtd-kpi"><span>${l}</span><b>${fmt(v)}</b><em>${d}</em></div>`).join("");
    document.getElementById("mtd-ta").textContent = `${st.sel} · ahead or behind ${MN[st.c-1]}, month to date`;
    document.getElementById("mtd-tb").textContent = `${st.sel} · each day, ${MN[CUR-1]} vs ${MN[st.c-1]}`;
    document.getElementById("mtd-lcur").textContent = MN[CUR-1]; document.getElementById("mtd-lcmp").textContent = MN[st.c-1];
    document.getElementById("mtd-ft").textContent = `By store · ${MEAS[st.m].toLowerCase()}, ${MN[CUR-1]} 1–${THRU} vs the same days`;
    document.getElementById("mtd-fp").textContent = `Plan the rest of ${MN[CUR-1]} · odds and daily targets`;
    prep(); drawA(); drawB(); stores(); plan();
  }
  render();
})();
</script>
'''

p = sys.argv[1]
s = open(p).read()
# remove any earlier copy, so the script can be re-run
s = re.sub(r'\n/\* ---- month to date \(MTD\) ---- \*/.*?(?=\n</style>)', '', s, count=1, flags=re.S)
s = re.sub(r'<section class="mtd" id="mtd">.*?</section>\n', '', s, count=1, flags=re.S)
s = re.sub(r'\n<script>\n/\* ---- month to date section.*?</script>\n', '\n', s, count=1, flags=re.S)
s = s.replace('\n</style>', CSS + '</style>', 1)
anchor = '<header>\n  <p class="eyebrow" id="latestline">'
assert anchor in s
s = s.replace(anchor, HTML + '\n' + anchor, 1)
assert s.count('</body>') == 1
s = s.replace('</body>', JS + '</body>', 1)
open(p, 'w').write(s)
print('ok')
