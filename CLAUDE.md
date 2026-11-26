# Scenthound revenue tracker

This repo holds the revenue trackers for Bryan Cottle's Scenthound scenters. He is a multi-unit franchisee in South Florida with two groups:

- **Broward+**: Plantation, Cooper City (opens Dec 2, 2026), PBG East, PBG Northlake.
- **Palm Beach County** (BCKK, with partners Chris and Tony): Wellington, Lake Worth, West Palm Beach, Boynton Beach, Boca Raton West.

GitHub `bcottlev/sh-plantation-revenue-tracker`. Every push to `main` deploys to Netlify at https://plantation-tracker.netlify.app.

## Rules that always apply

- **Never send a message to anyone without Bryan's explicit approval.** This covers Slack, text and email. Draft it, show it to him and wait for a yes. That includes bonus messages to managers. A bot workflow that already posts on a schedule is fine; a new one-off post is not.
- **Every data update ends with the comparison table** from `python3 tools/compare_table.py`: "[Month] 1–[latest day] compared with the same days in past months". It has each store vs the prior three months, sorted by this month's revenue (highest first), plus Total system and Palm Beach County rows.
- When you deliver an HTML page, say which file to open; Bryan opens it in his browser. Don't just paste a URL.
- **Slack-facing text:**
  - plain and short, no em dashes
  - write "scenter", never "center"
  - Slack doesn't render pasted tables, so use plain lines, and vertical ladders in the form `X = $Y`
- **Role names:** MA is now Wellness Coordinator. VMA is now VWC (Virtual Wellness Coordinator); the page and scripts say VWC everywhere (11/26), though Slack channels may still say VMA. Alina, the Plantation manager, shows up in Slack as "Nina Mariel".
- **MyTime is the revenue source of truth.** Never enter an estimated figure.

## Daily workflow: Bryan says "uploaded new data"

MyTime exports (Reports → Revenue Time Series → CSV) land in his iCloud folder:

`~/Library/Mobile Documents/com~apple~CloudDocs/Investments/Scenthound/Administration /AI/Revenue Analysis/`

There is a space before `/AI`. Usually there are two new files: one for all stores and one for PBG (file names end in `PBG` or `pga`). Take the newest files by modified time; the 5-digit number in the name increases with each export.

```bash
git pull --rebase
python3 tools/merge_exports.py "<folder>/revenue_time_series.NNNNN.csv" "<folder>/revenue_time_series.NNNNN PBG.csv"
python3 tools/refresh_pages.py          # month trackers, day-of-week data, store tiles, planner copy
python3 tools/compare_table.py          # paste this table in your reply
git add -A data day-of-week planner november stores && git commit -m "Data through MM/DD" && git push
```

- **Merge rule:** each export replaces its own date range for its own locations.
- **Late or early exports:** if an export was saved before 9 PM ET on its last date, that day may be partial and `merge_exports.py` warns. Bryan's call; usually keep the day and say it may change. Use `--drop-open-day` to leave it out.
- **Safety check:** `refresh_pages.py` aborts if any row from a previous month would change.

### Bryan says "pull the data": export it yourself

Follow `/pull-data`: export Daily Revenue (detailed CSV) from MyTime in Bryan's Chrome for the 6 stores on the main login, then ask Bryan to **Switch User** to the separate PBG login for PBG East and Northlake. You can't type passwords, so he switches and you wait. Move the files from `~/Downloads` into the Revenue Analysis folder and run the daily workflow above.

### What to report after an update

Keep it short. Cover:

- **Data range:** through which date, and anything partial.
- **Comparison table:** paste it.
- **Pace:** how many stores are on pace, and the biggest gaps. Read them from the store tiles, or compute them from the same model.
- **Data flags:** for example, a day far below normal for that store.

## Pages

| Path | What it is |
|---|---|
| `day-of-week/index.html` | Main page. The top section is month to date: store tiles, then a Trends fold. The bottom is the weekday analysis (time window, single month, measure, dot chart, by-day/week/month folds). |
| `<month>/index.html` | Plantation month pace tracker (`const dailyRevenue = {...}`, `const targetTotal`). |
| `stores/<slug>/<month>/index.html` | The same tracker for PBG East, PBG Northlake and Cooper City. |
| `planner/index.html` | Standalone copy of the month-to-date section. It is also the claude.ai artifact "November MTD Planner"; Bryan updates that one in claude.ai. |
| `data/mytime.csv` | Every MyTime row merged so far. Do not hand-edit it. |
| `month_totals.json` | Closed-month totals, read by the Slack report. |

### Day-of-week page internals

- **Order:** MTD section (tiles, one column always), Store health, then `<div class="sect" id="weekday">` (the weekday analysis, collapsible), Outreach, Outreach by role, then the By day / By week / All locations folds. Both section builders insert before the next block's anchor, so the order holds on re-runs.
- **Top bar** always says "Scenthound SFL"; the weekday title shows the selected store.
- **Folds:** `.fold[aria-controls]` toggles its body and remembers the choice per browser. Big sections use `data-open="1"` to start open until the viewer closes them. Store health, weekday analysis, Outreach and Outreach by role are big folds.
- **No footer notes:** Bryan removed the billing-day and source notes, and the long explanation under the tiles; don't add them back. Explanations go in hover titles.
- **Class names:** the outreach chart uses `.wk` for weekend bars. Tile classes are `.tw*`; don't reuse short names that the base page already styles.

`DATA_BY_LOC` holds `{"Store": [["MM-DD", weekday 0=Mon..6=Sun, net, nonmembership, batch 1=billing day], ...]}`. It is rebuilt from `data/mytime.csv` by `tools/build_dow.py` and spliced in by `refresh_pages.py`.

The month-to-date section (CSS, HTML and JS) lives entirely in **`tools/add_mtd_section.py`**. Edit it there and re-run `python3 tools/add_mtd_section.py day-of-week/index.html`; it is idempotent. Then run `tools/build_planner.py`. Never edit the section directly in the HTML, because the next refresh overwrites it.

- **Store tiles:** sorted by gap at pace, worst first.
  - Collapsed tile:
    - "±$X.Xk at pace": projected month end minus target. Green if it clears the target, amber if within 5% short, red otherwise.
    - The latest day vs the same day a week earlier.
    - A progress bar of month to date / target. Its tick is the weighted expected-to-date: the store's own weekday normals plus the 1st's membership billing.
  - Expanded tile:
    - This week vs the same weekday 1, 2 and 3 weeks back; a dashed outline marks a day that fell in last month.
    - Matching-days total and data warnings.
    - Daily targets for the rest of the month.
    - "Copy for Slack", which only copies; Bryan reviews before sending.
    - "Weekday analysis ↓", which switches the lower view to that store.
- **Model** (`wstats`, `model`):
  - Each store's last 42 days give per-weekday mean, p25 and p75. Billing days and the 1st are excluded.
  - Closed days: Thanksgiving, 12/25 and 1/1. The day before Thanksgiving, 12/24 and 12/31 are planned like a Saturday.
  - `CLOSED_DOW` lists stores closed on a weekday; PBG Northlake is closed Sundays.
  - Daily target = round(normal × max(lift, 1)).
- **Collapsed tile is 3 rows** (Bryan wants them compact): name · latest day vs a week earlier · gap at pace; the progress bar; MTD of target · floor $/day · vs prior months.
- **Floor figure on each tile:** average net per traded day, leaving out the 1st's billing, vs all of last month. Hidden under $200/day (Cooper City presale).
- **Store health section** (after the tiles), built by **`tools/add_health_section.py`** from `data/mytime.csv` (ticket level) and re-run by `refresh_pages.py`. Edit it there, never in the HTML.
  - Membership health cards: members billed on the 1st by month (7 months), change since 3 months ago, peak, new membership sales per 30 days. Shrinking/growing = 5% or more over 3 months; headline names the shrinking stores.
  - Store scorecard fold: floor $/day, visits/day (service tickets), average service ticket (gross), discount % of services, members, each with change vs last month and a 7-month bar sparkline. Cooper City left out until it opens.
  - PBG East bills many members on sign-up dates, so its 1st-of-month count is only part of its base; the card says so.
  - It hides the weekday view's "By month" fold, which the scorecard replaces.
- **Trends fold:** measure and compare-month controls, KPIs, chart A (running gap vs the comparison month: green ahead, red behind, future days faded) and chart B (daily pairs). A store chip picks what is charted.
- **Dark mode:** neutral charcoal, `body.dark` variables. Bryan dislikes navy and orange in dark mode; keep Skye blues and soft Daisy yellow.
- **Brand colors:** Skye `#2F9BD7`-family blues, Daisy yellow, Shadow navy text.
- **Testing:** check pages headless with Playwright. Look for page errors and for `scrollWidth` wider than the viewport at 390px and at 1280px, in light and dark mode.

## Targets: keep one source

| Store | Monthly target | Basis |
|---|---|---|
| Plantation | $34,000 | Alina's bonus target |
| PBG East | $28,500 | Tori's bonus target |
| PBG Northlake | $17,000 | Tori's bonus target |
| Others | prior month × 1.1, rounded to $100 | default |

- **Where they live today:**
  - `DEF_T` in `tools/add_mtd_section.py`
  - `const targetTotal` in each month tracker
- **Open issue:** the claude.ai daily digest routine uses August +10%, so Wellington shows $46,449 there and $50,100 on the page.
- **Bryan's decision:** one source for the page, the Slack bot and the digest. A good next step is a `data/targets.json` read by all three.
- **Still to confirm:** Bryan has not confirmed Palm Beach County targets; October +10% makes Wellington and West Palm Beach unreachable.

## Netlify credits: deploy sparingly

Netlify paused production deploys on 11/24/2026 after the account ran out of credits (billing cycle runs the 8th to the 7th). Every production deploy costs credits.

- **Netlify builds from GitHub itself.** The `deploy-netlify.yml` Action duplicated every deploy and is disabled (`gh workflow disable`). Don't re-enable it.
- **`netlify.toml` `ignore`** skips the deploy when a push only touches data, tools, scripts, `.txt`/`.md` files, `.claude`, `.github` or `month_totals.json`. Pages don't fetch those files; if a page ever starts to, update the rule.
- **Batch your pushes.** Iterate on design locally (headless checks, preview file) and push once when Bryan approves, not after each tweak. One push per data update.
- **After pushing, check the deploy went live:** `curl -s https://plantation-tracker.netlify.app/day-of-week/ | grep -c "<something new>"`, or the Netlify deploys page. A green `git push` doesn't mean the site updated.

## Automation (GitHub Actions)

| Workflow | What it does |
|---|---|
| `daily-slack-report.yml` | "Revenue Bot" posts in #plantation-revenue-updates `C0C9WCYKX8A`, #pbg-revenue-updates `C0CBZGMS9MW` and #cooper-city-revenue-updates `C0CAZSK43V3`. Day N comes from the latest entry's calendar day. Known issue: PBG East's projection is overstated because day 1 is treated as billing. |
| `eos-reminder.yml` + `eos_reminder.py` | At 8 PM it posts a one-line note to a store channel only when a manager End-of-Shift SM report is missing (last 7 days). Tags: Tori for both PBG stores; Nina and Holly for Plantation; Cooper City (Nina) from Dec 2. Input `post` defaults to false. |
| `pull-eos-desk.yml`, `pull-slack-revenue.yml` | Desk roster and manager revenue from the Slack reports. |
| `fact-api-daily.yml`, `ringcentral-archive.yml` | Corporate FACT API pull and RingCentral call archive. |
| `update-tracker.yml` | Tracker entry. |
| `deploy-netlify.yml` | Disabled since 11/26/2026; Netlify's own GitHub link deploys. |

- **Manual runs:** dispatch with `gh workflow run <file> -f post=true` and read logs with `gh run view --log`.
- **Scheduled tasks in claude.ai, not here:**
  - the 8 PM dispatch of the EOS reminder (`trig_01XfuLQeyrW7onNrbLXG99DB`)
  - the daily digest (`trig_01DYXaXGKk9JCnBomEApbqUh`)

  Changing them happens in claude.ai.
- **Other sessions:** other Claude sessions also commit here, for example "Update EOS desk roster…". Always `git pull --rebase` before you start. If `data/mytime.csv` has uncommitted changes you didn't make, ask before discarding them.

## Other tools

- **Plantation month-end reconciliation:** `tools/reconcile_month.py`.
- **New month tracker:** `tools/new_month.py REPO YYYY-MM TARGET [--compare=YYYY-MM]`. Ask Bryan for the target.
- **One day's figure:** `update_trackers.py REPO YYYY-MM-DD AMOUNT [slug]`.

## Open items to offer, not to do unasked

- **Targets:** one targets file, and Bryan to confirm the Palm Beach County targets.
- **Slack bot:** PBG East's projection in the Slack bot is overstated.
- **Boca Raton West:** missing from the MyTime exports; ask Bryan for an export that includes it.
- **Cooper City:** opens Dec 2. Create its December tracker and turn on its EOS reminder from that date.
- **Store schedules:** Plantation is open 7 days. Some Palm Beach County stores take little or nothing on Mondays (West Palm Beach averages about $110), so check that store's own Monday normal before flagging a low Monday.
