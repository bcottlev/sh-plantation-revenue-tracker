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

.mtd-tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,420px),1fr));gap:12px;margin:16px 0 6px;align-items:start}
.tile{background:var(--skye-8);border-radius:14px;padding:14px 16px 12px;border:1px solid transparent}
.tile.open{border-color:var(--line)}
.tile .th{display:flex;justify-content:space-between;align-items:baseline;gap:10px;cursor:pointer;background:none;border:0;padding:0;width:100%;text-align:left;font:inherit;color:inherit}
.tile .th:focus-visible{outline:2px solid var(--skye);outline-offset:3px;border-radius:6px}
.tile .tn{font-size:18px;font-weight:700;color:var(--shadow)}body.dark .tile .tn{color:var(--ink)}
.tile .tn i{font-style:normal;display:inline-block;margin-left:6px;font-size:12px;color:var(--mute);transition:transform .15s}
.tile.open .tn i{transform:rotate(180deg)}
.tile .gap{font-size:15px;font-weight:600;white-space:nowrap;font-variant-numeric:tabular-nums}
.tile .gap.g{color:var(--great)}.tile .gap.a{color:#C98A00}.tile .gap.r{color:var(--bad)}
body.dark .tile .gap.a{color:#E6B84A}
.tile .ld{font-size:14px;color:var(--ink-70);margin:3px 0 8px;font-variant-numeric:tabular-nums}
.tile .ld .flag{color:var(--bad);font-weight:600}
.tile .pb{position:relative;height:8px;background:var(--skye-20);border-radius:5px;margin:4px 0 7px}
.tile .pb .f{position:absolute;left:0;top:0;bottom:0;border-radius:5px}
.tile .pb .f.g{background:var(--great)}.tile .pb .f.a{background:#E0A82E}.tile .pb .f.r{background:var(--bad)}
.tile .pb .k{position:absolute;top:-4px;width:2px;height:16px;background:var(--ink-70);margin-left:-1px;border-radius:1px}
.tile .ft{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;font-size:13px;color:var(--mute);font-variant-numeric:tabular-nums}
.tile .body{display:none;margin-top:12px;padding-top:12px;border-top:1px solid var(--line)}.tile.open .body{display:block}
.wk-leg{font-size:12.5px;color:var(--ink-70);margin-bottom:6px}.wk-leg i{display:inline-block;width:11px;height:11px;border-radius:3px;margin:0 5px -1px 0}.wk-leg>span{white-space:nowrap;margin-right:12px;display:inline-block}
.wk{display:grid;grid-template-columns:76px minmax(0,1fr) auto;gap:4px 10px;align-items:center;font-variant-numeric:tabular-nums}
.wk .dl{font-size:13.5px;color:var(--ink)}
.wk .bars{position:relative;display:flex;flex-direction:column;gap:3px;padding:3px 0}
.wk .bars b{display:block;height:5px;border-radius:3px;min-width:2px;position:relative}.wk .bars b.c{height:10px;background:var(--skye)}
.wk .bars b.w1,.wk-leg i.w1{background:#8C9AA8}.wk .bars b.w2,.wk-leg i.w2{background:#B3BFCA}.wk .bars b.w3,.wk-leg i.w3{background:#D2DAE2}
body.dark .wk .bars b.w1,body.dark .wk-leg i.w1{background:#8A8984}body.dark .wk .bars b.w2,body.dark .wk-leg i.w2{background:#B5B3AC}body.dark .wk .bars b.w3,body.dark .wk-leg i.w3{background:#DAD8D1}
.wk .bars b.lm,.wk-leg i.lm{background:transparent;border:1.5px dashed var(--mute);box-sizing:border-box}.wk .bars b.lm{height:7px}
.wk .bars b.lm span{position:absolute;left:100%;top:50%;transform:translateY(-50%);margin-left:6px;font-size:11.5px;color:var(--mute);white-space:nowrap;font-weight:400}
.wk .dl,.wk .vv{align-self:start;padding-top:1px}.wk{row-gap:9px}
.wk .bars u{position:absolute;top:0;bottom:0;width:0;border-left:1.5px dashed;text-decoration:none;opacity:.7}.wk .bars u.l{border-color:var(--bad)}.wk .bars u.h{border-color:var(--great)}
.wk .vv{font-size:13.5px;text-align:right;white-space:nowrap;color:var(--ink)}.wk .vv em{font-style:normal;font-weight:600;margin-left:6px}
.wk .vv em.up{color:var(--great)}.wk .vv em.down{color:var(--bad)}
.wk-ax{position:relative;height:16px;margin:2px 0 0 86px;font-size:11px;color:var(--mute)}.wk-ax span{position:absolute;transform:translateX(-50%)}.wk-ax span:last-child{transform:translateX(-100%)}.wk-ax span:first-child{transform:none}
.wk-ax .l{color:var(--bad);font-weight:600}.wk-ax .h{color:var(--great);font-weight:600}
.tile .sum{font-size:13.5px;color:var(--ink-70);margin:10px 0 4px}
.tile .warn{font-size:12.5px;color:var(--bad);margin:2px 0}
.tile .sub2{font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--mute);margin:14px 0 6px}
.tile .mtd-days{grid-template-columns:repeat(auto-fill,minmax(104px,1fr))}
.tile .acts{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:10px}
.mtd-ghost{font:inherit;font-size:13.5px;font-weight:600;padding:8px 14px;border-radius:999px;border:1.5px solid var(--line);background:transparent;color:var(--ink);cursor:pointer}
.mtd-ghost:hover{border-color:var(--skye)}
@media (max-width:560px){.wk .dl .md{display:none}.wk{grid-template-columns:50px minmax(0,1fr) auto}.wk-ax{margin-left:60px}.tile .mtd-days{grid-template-columns:repeat(3,minmax(0,1fr))}}

/* ---- dark mode, neutral (Claude-style) instead of navy ---- */
body.dark{--ink:#F5F4EF;--ink-70:#C2C0B6;--mute:#9C9A92;--line:#3A3936;--white:#1F1E1D;--skye-8:#262624;--skye-20:#34332F;--skye-45:#5E5D59;--shadow:#E8E6DF;background:#1F1E1D;
  --skye:#5BB0E3;--daisy:#E6D466;--great:#7FB685;--great-soft:rgba(127,182,133,.16);--bad:#E26D6D;--bad-soft:rgba(226,109,109,.14)}
/* accents: Skye blue (lightened for dark) with a soft Daisy, neutrals for selection */
body.dark .tab{background:#30302E;color:#F5F4EF}
body.dark .bar{border-bottom-color:var(--line)}body.dark .mtd{border-bottom-color:var(--line)}
body.dark .seg button[aria-pressed="true"]{background:#F5F4EF;border-color:#F5F4EF;color:#1F1E1D}
body.dark .switch[aria-checked="true"]::after{background:#1F1E1D}
body.dark header .eyebrow{color:var(--skye)}
body.dark .avgmark,body.dark .k-bar{background:#F5F4EF}
body.dark .span,body.dark .k-wd{background:#4A8DB8}body.dark .rowline.wknd .span,body.dark .k-wk{background:var(--daisy)}
body.dark .mtd-trk .rg{background:rgba(91,176,227,.38);opacity:1}
body.dark .mtd-trk .tg{background:#F5F4EF;box-shadow:none}
body.dark .mtd-st.reach{background:#34332F;color:#F5F4EF}body.dark .mtd-st.str{background:rgba(230,212,102,.16);color:#E6D466}
body.dark .mtd-copy{background:#5BB0E3;border-color:#5BB0E3;color:#1F1E1D}
body.dark .mtd-day.next{border-color:#F5F4EF}
body.dark .seg[data-role="MA"],body.dark .track .tlab i.ma{background:#5BB0E3!important}
body.dark .seg[data-role="VMA"],body.dark .track .tlab i.vma{background:#C2C0B6!important}
body.dark .dot.latest{border-color:#1F1E1D}body.dark .k-latest{border-color:#1F1E1D}
body.dark .tip{background:#3A3936;color:#F5F4EF;box-shadow:0 4px 14px rgba(0,0,0,.55)}body.dark .tip::after{background:#3A3936}
body.dark .tip b{color:#fff}body.dark .tip .mgr,body.dark .tip .who{border-top-color:rgba(255,255,255,.15)}
body.dark .tip .mgr .ops,body.dark .tip .who .vma{color:rgba(255,255,255,.7)}body.dark .tip .who.none{color:rgba(255,255,255,.55)}
body.dark .tip .v.bad{color:#FFB3A6}body.dark .tip .v.great{color:#9FE3BE}
body.dark .mtd-tip{background:#30302E;border-color:#3A3936;box-shadow:0 4px 14px rgba(0,0,0,.5)}
body.dark .mtd-trk .mt{background:#C2C0B6}body.dark .mtd-day.next{background:#30302E}
body.dark .mtd-t tr.grp td{border-top-color:#5A5955}body.dark .mtd-pre{background:#262624}
@media (max-width:560px){
 .mtd-row{grid-template-columns:minmax(0,1fr);gap:5px}.mtd-row .rt{text-align:left}.mtd-axis .rt,.mtd-axis>div:first-child{display:none}
 .mtd-days{grid-template-columns:repeat(3,minmax(0,1fr))}
 .mtd-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}
 .mtd-t td{font-size:13px}.mtd-t th{font-size:10px;letter-spacing:.08em}.mtd-t .mtd-bar{display:none}
}
'''

HTML = r'''<section class="mtd" id="mtd">
  <p class="eyebrow" id="mtd-eyebrow"></p>
  <h2 class="mtd-h" id="mtd-head"></h2>
  <p class="range" id="mtd-sub"></p>
  <div class="mtd-tiles" id="mtd-tiles"></div>
  <p class="mtd-note" id="mtd-tnote"></p>
  <p class="eyebrow fold" role="button" tabindex="0" aria-controls="mtd-trends" aria-expanded="false" id="mtd-ft"></p>
  <div id="mtd-trends" class="fbody">
    <div class="controls">
      <div class="ctlrow">
        <div class="ctl"><p class="eyebrow">Measure</p><div class="seg" id="mtd-meas" role="group" aria-label="MTD measure"></div></div>
        <div class="ctl"><p class="eyebrow">Compare to</p><div class="seg" id="mtd-cmp" role="group" aria-label="Compare month"></div></div>
      </div>
      <div class="ctl"><p class="eyebrow">Chart</p><div class="seg" id="mtd-sel" role="group" aria-label="Store to chart"></div></div>
    </div>
    <div class="mtd-kpis" id="mtd-kpis"></div>
    <div class="mtd-card">
      <header><strong id="mtd-ta"></strong><span class="mtd-leg"><i style="background:var(--great)"></i>Ahead<i style="background:var(--bad)"></i>Behind<i class="fut"></i>Days to come</span></header>
      <div class="mtd-fig" id="mtd-fa"><svg id="mtd-sa" role="img" aria-label="Running gap versus comparison month"></svg><div class="mtd-tip" id="mtd-pa" hidden></div></div>
    </div>
    <div class="mtd-card">
      <header><strong id="mtd-tb"></strong><span class="mtd-leg"><i style="background:var(--skye)"></i><span id="mtd-lcur"></span><i style="background:var(--skye-45)"></i><span id="mtd-lcmp"></span><i class="fut"></i>Days to come</span></header>
      <div class="mtd-fig" id="mtd-fb"><svg id="mtd-sb" role="img" aria-label="Daily revenue, this month versus comparison month"></svg><div class="mtd-tip" id="mtd-pb" hidden></div></div>
      <p class="mtd-note">Hover or tap either chart for that day.</p>
    </div>
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
  // ---------- store tiles ----------
  const netOn = (s, dt) => { const g = G[s][dt.getMonth()+1]; return g && g.has[dt.getDate()-1] ? g.net[dt.getDate()-1] : null; };
  const lastDate = s => { const r = DATA_BY_LOC[s][DATA_BY_LOC[s].length-1]; return new Date(YEAR, +r[0].slice(0,2)-1, +r[0].slice(3,5)); };
  const addD = (dt, n) => new Date(dt.getFullYear(), dt.getMonth(), dt.getDate() + n);
  const lab = dt => DNS[dt.getDay()] + " " + (dt.getMonth()+1) + "/" + dt.getDate();
  function expShare(s){                                  // weighted share of the month's revenue normally booked by THRU
    const W = wstats(s), dim = DIM(CUR), prev = G[s][CUR-1];
    const w = d => { if (d === 1) return prev ? prev.net[0] : W[wdIdx(new Date(YEAR, CUR-1, 1))].m;
      const dt = new Date(YEAR, CUR-1, d), k = kind(s, dt); return k === "closed" ? 0 : W[k === "sat" ? 5 : wdIdx(dt)].m; };
    let a = 0, t = 0; for (let d = 1; d <= dim; d++) { const x = w(d); t += x; if (d <= THRU) a += x; } return t ? a / t : THRU / dim;
  }
  function tileData(s){
    const m = model(s), proj = m.mid, diff = proj - m.T.t, cls = diff >= 0 ? "g" : diff >= -0.05 * m.T.t ? "a" : "r";
    const ld = lastDate(s), lv = netOn(s, ld) ?? 0, pv = netOn(s, addD(ld, -7));
    const W = wstats(s), flags = [];
    for (let i = 6; i >= 0; i--) { const dt = addD(ld, -i); if (dt.getDate() === 1) continue; const v = netOn(s, dt), k = kind(s, dt), nrm = W[wdIdx(dt)].m;
      if (k !== "closed" && nrm > 300 && (v == null || v < nrm * 0.4)) flags.push(`${lab(dt)} shows ${fmt(v || 0)} (normal ${fmt(nrm)}): store closed, or sales missing from the export?`); }
    const cmp = CMPS.slice(0,2).map(mm => { const a = sum([s], CUR, THRU), b = has(s, mm) ? sum([s], mm, THRU) : 0; return b ? `vs ${MN[mm-1]} ${pct(a,b) > 0 ? "+" : ""}${pct(a,b)}%` : null; }).filter(Boolean);
    return {m, proj, diff, cls, ld, lv, pv, flags, cmp, share: expShare(s)};
  }
  const kd = v => (v >= 0 ? "+" : "−") + "$" + (Math.abs(v)/1000).toFixed(1) + "k";
  let OPEN = {}; try { OPEN = JSON.parse(localStorage.getItem("dow.tiles") || "{}"); } catch (e) {}
  const TXT = {};
  function weekRows(s, ld){
    const rows = []; for (let i = 6; i >= 0; i--) { const dt = addD(ld, -i); if (dt.getDate() === 1) continue;
      const back = [1,2,3].map(w => { const d = addD(dt, -7*w); return {w, d, v: d.getDate() === 1 ? null : netOn(s, d), lm: d.getMonth() !== dt.getMonth()}; });
      rows.push({dt, c: netOn(s, dt), back, p: back[0].v}); }
    const mx0 = Math.max(1000, ...rows.flatMap(r => [r.c || 0, ...r.back.map(x => x.v || 0)])), mx = Math.ceil(mx0 / 500) * 500, P = v => Math.max(0, Math.min(100, v / mx * 100));
    const html = rows.map(r => { const ch = r.c != null && r.p ? Math.round((r.c / r.p - 1) * 100) : null;
      const bk = r.back.filter(x => x.v != null).map(x => x.lm
        ? `<b class="lm" style="width:${P(x.v)}%"><span>${MN[x.d.getMonth()]} ${x.d.getDate()}</span></b>`
        : `<b class="w${x.w}" style="width:${P(x.v)}%" title="${lab(x.d)}: ${fmt(x.v)}"></b>`).join("");
      return `<div class="dl">${DNS[r.dt.getDay()]} <span class="md">${r.dt.getMonth()+1}/</span>${r.dt.getDate()}</div><div class="bars"><u class="l" style="left:${P(500)}%"></u><u class="h" style="left:${P(1000)}%"></u><b class="c" style="width:${P(r.c || 0)}%" title="${lab(r.dt)}: ${fmt(r.c || 0)}"></b>${bk}</div>
        <div class="vv">${r.c == null ? "—" : fmt(r.c)}${ch == null ? "" : `<em class="${ch >= 0 ? "up" : "down"}">${ch > 0 ? "+" : ""}${ch}%</em>`}</div>`; }).join("");
    const ax = [0, 500, 1000, mx].filter((v,i,a) => a.indexOf(v) === i).map(v => `<span class="${v === 500 ? "l" : v === 1000 ? "h" : ""}" style="left:${P(v)}%">${fmt(v)}</span>`).join("");
    const both = rows.filter(r => r.c != null && r.p != null), sc = both.reduce((a,r) => a + r.c, 0), sp = both.reduce((a,r) => a + r.p, 0);
    return {html, ax, sc, sp};
  }
  function tiles(){
    const T = STORES.map(s => ({s, ...tileData(s)})).sort((a,b) => a.diff - b.diff);
    const on = T.filter(t => t.cls === "g").length, sysProj = T.reduce((a,t) => a + t.proj, 0), sysT = T.reduce((a,t) => a + t.m.T.t, 0);
    document.getElementById("mtd-head").textContent = `${on} of ${T.length} stores on pace to hit target`;
    const n = sum(STORES, CUR, THRU), c = sum(STORES, CMPS[0], THRU);
    // weekday-matched: last month's average for each weekday, times this month's count of that weekday (the 1st compared to the 1st)
    const wm = (() => { const pm = CMPS[0]; let e = 0; STORES.forEach(s => { const g = G[s][pm]; if (!g) return; const by = Array.from({length:7}, () => []);
      for (let d = 2; d <= DIM(pm); d++) if (g.has[d-1]) by[wdIdx(new Date(YEAR, pm-1, d))].push(g.net[d-1]);
      e += g.net[0]; for (let d = 2; d <= THRU; d++) { const l = by[wdIdx(new Date(YEAR, CUR-1, d))]; if (l.length) e += l.reduce((a,b) => a+b, 0) / l.length; } }); return e; })();
    document.getElementById("mtd-sub").innerHTML = `System ${fmt(n)} month to date · projected <b>${fmt(sysProj)}</b> vs ${fmt(sysT)} target · vs ${MN[CMPS[0]-1]} ${pc(pct(n, c))} (same dates) / ${pc(pct(n, wm))} weekday-matched`;
    document.getElementById("mtd-tiles").innerHTML = T.map((t, i) => {
      const m = t.m, wk = weekRows(t.s, t.ld), fill = Math.min(100, m.mtd / m.T.t * 100), lc = t.pv ? Math.round((t.lv / t.pv - 1) * 100) : null;
      const S = d => lab(d.dt);
      const big = Math.max(...m.days.map(x => x.tgt), 0);
      const days = m.days.map(x => x.k === "closed" ? `<div class="mtd-day closed"><div class="w">${S(x)}</div><div class="v">closed</div><div class="x">${x.d === thanks(CUR) && CUR === 11 ? "Thanksgiving" : ""}</div></div>`
        : `<div class="mtd-day${x.tgt === big ? " big" : ""}"><div class="w">${S(x)}${x.k === "sat" ? " ★" : ""}</div><div class="v">${fmt(x.tgt)}</div><div class="x">${x.k === "sat" ? "holiday eve" : "normal " + fmt(x.base)}</div></div>`).join("");
      TXT[t.s] = `*${t.s} · ${MN[CUR-1]} targets*\nSo far: ${fmt(m.mtd)} · Target: ${fmt(m.T.t)}${m.gap > 0 ? ` · ${fmt(m.gap)} to go` : " ✅"}\n` + m.days.filter(x => x.k !== "closed").map(x => `${S(x)}: ${fmt(x.tgt)}${x.k === "sat" ? " (holiday eve)" : ""}`).join("\n");
      return `<div class="tile${OPEN[t.s] ? " open" : ""}" data-s="${t.s}">
        <button type="button" class="th" aria-expanded="${!!OPEN[t.s]}"><span class="tn">${t.s}<i>▾</i></span><span class="gap ${t.cls}">${kd(t.diff)} at pace</span></button>
        <div class="ld">${DNS[t.ld.getDay()]} ${fmt(t.lv)}${lc == null ? "" : ` · ${lc > 0 ? "+" : ""}${lc}% vs ${lab(addD(t.ld, -7))}`}${t.flags.length ? ` · <span class="flag">check data</span>` : ""}</div>
        <div class="pb" title="Tick = where the store normally is by the ${ord(THRU)} (${Math.round(t.share*100)}% of target)"><span class="f ${t.cls}" style="width:${fill}%"></span><span class="k" style="left:${Math.min(100, t.share*100)}%"></span></div>
        <div class="ft"><span>${fmt(m.mtd)} of ${fmt(m.T.t)} (${(m.mtd / m.T.t * 100).toFixed(1)}%)</span><span>${t.cmp.join(" · ")}</span></div>
        <div class="body">
          <div class="wk-leg"><span><i style="background:var(--skye)"></i>This week</span><span><i class="w1"></i>1 wk ago</span><span><i class="w2"></i>2 wks ago</span><span><i class="w3"></i>3 wks ago</span><span><i class="lm"></i>Last month</span></div>
          <div class="wk">${wk.html}</div><div class="wk-ax">${wk.ax}</div>
          <p class="sum">Matching days ${fmt(wk.sc)} vs ${fmt(wk.sp)} the week before ${wk.sp ? pc(pct(wk.sc, wk.sp)) : ""}</p>
          <p class="mtd-note">Gray bars are the same weekday 1, 2 and 3 weeks back; a dashed outline means that day fell in last month. % is vs 1 week ago. The 1st (billing day) is left out.</p>
          ${t.flags.map(f => `<p class="warn">⚠ ${f}</p>`).join("")}
          <p class="sub2">Rest of ${MN[CUR-1]} · ${m.gap > 0 ? `${fmt(m.gap)} to go, ${liftTxt(m).replace(/<\/?b>/g, "")}` : "target reached"} · target ${m.T.src}</p>
          <div class="mtd-days">${days || '<div class="mtd-day closed"><div class="v">month complete</div></div>'}</div>
          <div class="acts"><button type="button" class="mtd-copy" data-copy="${t.s}">Copy for Slack</button><button type="button" class="mtd-ghost" data-open="${t.s}">Weekday analysis ↓</button><span class="mtd-note" data-out="${t.s}"></span></div>
          <pre class="mtd-pre" data-pre="${t.s}" hidden></pre>
        </div></div>`; }).join("");
    document.getElementById("mtd-tnote").textContent = `Sorted by gap at pace, worst first. Bar = month to date as a share of target; tick = where the store normally is by the ${ord(THRU)}, weighted by its own weekdays and the 1st's billing. "At pace" = likely month end (each store's last 6 weeks, weekday by weekday${thanks(CUR) ? "; Thanksgiving closed, the day before planned like a Saturday" : ""}) minus target. Green clears target, amber within 5%, red more than 5% short. Targets: bonus targets for Plantation, PBG East and PBG Northlake; prior month +10% elsewhere.`;
  }
  function liftTxt(m){ return m.gap <= 0 ? "target already reached" : m.lift <= 0 ? `a normal week clears it by ${fmt(-m.lift * (m.mid - m.mtd))}` : `needs <b>${Math.round(m.lift*100)}% above</b> a normal week`; }
  document.getElementById("mtd-tiles").addEventListener("click", async e => {
    const th = e.target.closest(".th"); if (th) { const t = th.closest(".tile"), s = t.dataset.s; OPEN[s] = !OPEN[s]; t.classList.toggle("open", OPEN[s]); th.setAttribute("aria-expanded", OPEN[s]); try { localStorage.setItem("dow.tiles", JSON.stringify(OPEN)); } catch (er) {} return; }
    const cp = e.target.closest("[data-copy]"); if (cp) { const s = cp.dataset.copy, out = document.querySelector(`[data-out="${s}"]`), pre = document.querySelector(`[data-pre="${s}"]`);
      try { await navigator.clipboard.writeText(TXT[s]); out.textContent = "Copied. Review it before you send it."; pre.hidden = true; }
      catch (er) { pre.textContent = TXT[s]; pre.hidden = false; out.textContent = "Copy didn't work here; select the text below."; } return; }
    const op = e.target.closest("[data-open]"); if (op) { const b = document.querySelector(`#locseg button[data-loc="${op.dataset.open}"]`); if (b) b.click(); const h = document.getElementById("latestline"); if (h) h.scrollIntoView({behavior:"smooth", block:"start"}); }
  });
  function render(){
    seg("mtd-meas", Object.entries(MEAS), "m"); seg("mtd-cmp", CMPS.map(m => [m, MN[m-1]]), "c");
    seg("mtd-sel", [["Total system","Total system"], ...STORES.map(x => [x, x])], "sel");
    const n = sum(STORES, CUR, THRU);
    document.getElementById("mtd-eyebrow").textContent = `Month to date · ${MN[CUR-1]} 1–${THRU}, ${YEAR} · all scenters`;
    document.getElementById("mtd-kpis").innerHTML = [[CUR, n, MN[CUR-1] + " 1–" + THRU, "this month"], ...CMPS.map(m => { const v = sum(STORES, m, THRU); return [m, v, MN[m-1] + " 1–" + THRU, pc(pct(n, v)) + " vs " + MN[m-1]]; })]
      .map(([m,v,l,d]) => `<div class="mtd-kpi"><span>${l}</span><b>${fmt(v)}</b><em>${d}</em></div>`).join("");
    document.getElementById("mtd-ta").textContent = `${st.sel} · ahead or behind ${MN[st.c-1]}, month to date`;
    document.getElementById("mtd-tb").textContent = `${st.sel} · each day, ${MN[CUR-1]} vs ${MN[st.c-1]}`;
    document.getElementById("mtd-lcur").textContent = MN[CUR-1]; document.getElementById("mtd-lcmp").textContent = MN[st.c-1];
    document.getElementById("mtd-ft").textContent = `Trends · ${MEAS[st.m].toLowerCase()}, ${MN[CUR-1]} vs earlier months, day by day`;
    prep(); drawA(); drawB();
  }
  // data freshness in the top bar
  (function(){ const cr = document.querySelector(".bar .crumb"); if (!cr) return; const d = new Date(YEAR, CUR-1, THRU), now = new Date(), age = Math.floor((new Date(now.getFullYear(), now.getMonth(), now.getDate()) - d) / 864e5);
    cr.innerHTML = `Daily Revenue Tracker <span>· data through ${DNS[d.getDay()]} ${CUR}/${THRU}${age > 1 ? ` · <b style="color:var(--bad)">${age} days old</b>` : ""}</span>`; })();
  tiles();
  render();
  // outreach person colours: softer palette in dark mode, original in light
  if (typeof OCOLORS !== "undefined") {
    const LIGHTC = OCOLORS.slice(), DARKC = ["#5BB0E3","#C2C0B6","#E6D466","#7FB685","#8FA8D8","#9CCDEB","#B58BC4","#C9787F"];
    const sync = () => { const d = document.body.classList.contains("dark"); OCOLORS.splice(0, OCOLORS.length, ...(d ? DARKC : LIGHTC)); if (typeof renderOutreach === "function") renderOutreach(); };
    document.getElementById("themeswitch").addEventListener("click", sync); sync();
  }
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
