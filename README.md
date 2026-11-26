# sh-plantation-revenue-tracker

Revenue trackers for Bryan Cottle's Scenthound scenters, deployed to https://plantation-tracker.netlify.app.

Start with **CLAUDE.md**: workflows, page internals, targets, automation and house rules.

Quick start after new MyTime exports:

```bash
python3 tools/merge_exports.py <export.csv> [...]
python3 tools/refresh_pages.py
python3 tools/compare_table.py
```
