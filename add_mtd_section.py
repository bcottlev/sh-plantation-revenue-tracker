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
@media (max-width:560px){
 .mtd-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}
 .mtd-t td{font-size:13px}.mtd-t th{font-size:10px;letter-spacing:.08em}.mtd-t .mtd-bar{display:none}
 #mtd-plan thead{display:none}#mtd-plan tr{display:grid;grid-template-columns:1fr 1fr;gap:3px 12px;padding:10px 0;border-bottom:1px solid var(--line)}
 #mtd-plan td{border:0;padding:2px 0;display:flex;justify-content:space-between;align-items:center;gap:6px}
 #mtd-plan td::before{content:attr(data-l);color:var(--mute);font-size:11.5px}
 #mtd-plan td.nm{grid-column:1/-1;justify-content:flex-start}#mtd-plan td:empty{display:none}
 #mtd-plan tr.grp{border-top:2px solid var(--shadow)}#mtd-plan tr.grp td{border:0}
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
    <header><strong id="mtd-ta"></strong><span class="mtd-leg"><i style="background:var(--skye)"></i>Ahead<i style="background:var(--bad)"></i>Behind</span></header>
    <div class="mtd-fig" id="mtd-fa"><svg id="mtd-sa" role="img" aria-label="Running gap versus comparison month"></svg><div class="mtd-tip" id="mtd-pa" hidden></div></div>
  </div>
  <div class="mtd-card">
    <header><strong id="mtd-tb"></strong><span class="mtd-leg"><i style="background:var(--skye)"></i><span id="mtd-lcur"></span><i style="background:var(--skye-45)"></i><span id="mtd-lcmp"></span></span></header>
    <div class="mtd-fig" id="mtd-fb"><svg id="mtd-sb" role="img" aria-label="Daily revenue, this month versus comparison month"></svg><div class="mtd-tip" id="mtd-pb" hidden></div></div>
    <p class="mtd-note">Hover or tap either chart for that day. Tap a store in the table below to chart it.</p>
  </div>
  <p class="eyebrow fold" role="button" tabindex="0" aria-controls="mtd-stores" aria-expanded="false" id="mtd-ft"></p>
  <div id="mtd-stores" class="fbody"></div>
  <p class="eyebrow fold" role="button" tabindex="0" aria-controls="mtd-planbox" aria-expanded="false" id="mtd-fp"></p>
  <div id="mtd-planbox" class="fbody"><p class="mtd-note">Total revenue. Edit a target or open-days figure; the page remembers your numbers in this browser. Pace is the average of the last 14 trading days (billing day excluded). Open days left skip closed holidays and Northlake Sundays.</p><table class="mtd-t" id="mtd-plan"></table></div>
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
  let saved = {}; try { saved = JSON.parse(localStorage.getItem("dow.mtdplan") || "{}"); } catch (e) {}
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
  function xlab(o, x, bw, H){ for (const d of [1,8,15,22,29]) o.push(`<text x="${x(d)+bw/2}" y="${H-6}" text-anchor="middle" font-size="11" fill="var(--mute)">${d}</text>`); }
  function drawA(){
    if (!CH) return; const W = svgA.clientWidth, H = svgA.clientHeight; if (!W) return;
    const pl = W < 520 ? 42 : 54, pr = 8, pt = 10, pb = 22, g = CH.gap;
    const mx = Math.max(...g.map(Math.abs), 1) * 1.15, lo = Math.min(...g) < 0 ? -mx : -mx * .15, hi = Math.max(...g) > 0 ? mx : mx * .15;
    const bw = (W - pl - pr) / 31, x = d => pl + (d-1) * bw, y = v => pt + (hi - v) / (hi - lo) * (H - pt - pb);
    const o = []; axis(o, lo, hi, y, pl, W, pr);
    o.push(`<line x1="${pl}" x2="${W-pr}" y1="${y(0)}" y2="${y(0)}" stroke="var(--shadow)" stroke-width="1.2"/>`);
    g.forEach((v,i) => { const y0 = y(0), y1 = y(v); o.push(`<rect x="${(x(i+1)+bw*.15).toFixed(1)}" width="${(bw*.7).toFixed(1)}" y="${Math.min(y0,y1).toFixed(1)}" height="${Math.max(1,Math.abs(y1-y0)).toFixed(1)}" rx="2" fill="${v >= 0 ? "var(--skye)" : "var(--bad)"}"/>`); });
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
    const o = []; axis(o, lo, hi, y, pl, W, pr);
    for (let d = 1; d <= 31; d++) { const p = CH.dp[d-1], n = CH.dn[d-1];
      if (p != null) o.push(`<rect x="${(x(d)+bw*.1).toFixed(1)}" width="${w.toFixed(1)}" y="${Math.min(y(0),y(cl(p))).toFixed(1)}" height="${Math.max(1,Math.abs(y(cl(p))-y(0))).toFixed(1)}" rx="1.5" fill="var(--skye-45)"/>`);
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
  function openDays(s){ let n = 0; const dim = DIM(CUR); for (let d = THRU + 1; d <= dim; d++) { const dt = new Date(YEAR, CUR-1, d), k = String(CUR).padStart(2,"0") + "-" + String(d).padStart(2,"0"); if (HOLI.has(k) || (CLOSED_DOW[s] || []).includes(dt.getDay())) continue; n++; } return n; }
  function pace(s){ const rows = DATA_BY_LOC[s].filter(r => r[4] !== 1 && (+r[2] || 0) > 50); const l = rows.slice(-14); return l.length ? l.reduce((a,r) => a + (+r[2]), 0) / l.length : 0; }
  function plan(){
    const tot = s => { const g = G[s][CUR]; if (!g) return 0; let t = 0; for (let d = 0; d < THRU; d++) t += g.net[d]; return t; };
    const fullPrev = s => { const g = G[s][CUR-1]; return g ? g.net.reduce((a,b) => a + b, 0) : 0; };
    const R = STORES.map(s => { const mtd = tot(s), t = +(saved[s]?.t ?? DEF_T[s] ?? Math.round(fullPrev(s)/100)*100), d = +(saved[s]?.d ?? openDays(s)), p = pace(s), proj = mtd + p * d, need = d ? (t - mtd) / d : 0; return {s, mtd, t, d, p, proj, need, ok: proj >= t}; });
    const T = R.reduce((a,r) => ({mtd: a.mtd + r.mtd, t: a.t + r.t, proj: a.proj + r.proj}), {mtd:0, t:0, proj:0});
    document.getElementById("mtd-plan").innerHTML = `<thead><tr><th>Store</th><th>MTD</th><th>Target</th><th>Open days left</th><th>Need / open day</th><th>Recent pace</th><th>Projected</th><th></th></tr></thead><tbody>` +
      R.map(r => `<tr><td class="nm">${r.s}</td><td data-l="MTD">${fmt(r.mtd)}</td><td data-l="Target"><input inputmode="numeric" data-s="${r.s}" data-k="t" value="${r.t}" aria-label="${r.s} target"></td><td data-l="Open days left"><input class="d" inputmode="numeric" data-s="${r.s}" data-k="d" value="${r.d}" aria-label="${r.s} open days left"></td><td data-l="Need / open day"><b>${r.need > 0 ? fmt(r.need) : "done"}</b></td><td data-l="Recent pace">${fmt(r.p)}</td><td data-l="Projected">${fmt(r.proj)}</td><td data-l="vs target"><span class="mtd-pill ${r.ok ? "ok" : "no"}">${r.ok ? "on track" : fmt(r.proj - r.t)}</span></td></tr>`).join("") +
      `<tr class="grp"><td class="nm">Total</td><td data-l="MTD">${fmt(T.mtd)}</td><td data-l="Target">${fmt(T.t)}</td><td></td><td></td><td></td><td data-l="Projected">${fmt(T.proj)}</td><td data-l="vs target"><span class="mtd-pill ${T.proj >= T.t ? "ok" : "no"}">${T.proj >= T.t ? "on track" : fmt(T.proj - T.t)}</span></td></tr></tbody>`;
  }
  document.getElementById("mtd-plan").addEventListener("change", e => { const i = e.target; if (!i.dataset.s) return; const v = parseFloat(String(i.value).replace(/[^0-9.]/g, "")); if (isNaN(v)) return; (saved[i.dataset.s] ??= {})[i.dataset.k] = v; try { localStorage.setItem("dow.mtdplan", JSON.stringify(saved)); } catch (e) {} plan(); });
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
    document.getElementById("mtd-fp").textContent = `Plan the rest of ${MN[CUR-1]} · targets, pace and projection`;
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
