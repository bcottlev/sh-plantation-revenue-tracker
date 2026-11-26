Bryan uploaded new MyTime exports. Update everything and report.

1. `git pull --rebase`.
2. Find the newest `revenue_time_series.*.csv` files in the Revenue Analysis folder (see CLAUDE.md), usually one all-store file and one PBG file, by modified time. Say which files you used.
3. `python3 tools/merge_exports.py <files>`. If it warns that the last day may be partial, keep it and mention it, unless $ARGUMENTS says otherwise.
4. `python3 tools/refresh_pages.py`.
5. Check the day-of-week page headless (no page errors), then commit "Data through MM/DD" and push.
6. Reply briefly:
   - the data range, and anything partial
   - the table from `python3 tools/compare_table.py`
   - how many stores are on pace and the biggest gaps
   - data flags
   - that `planner/index.html` changed, if Bryan wants the claude.ai planner artifact refreshed
