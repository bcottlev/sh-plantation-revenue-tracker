Pull the latest MyTime exports yourself, then run the normal update. Bryan switches MyTime logins for the PBG part; you never type a password.

Use Claude in Chrome (Bryan's signed-in Chrome). Exports land in `~/Downloads`.

Date range: the last 3 days through today (or the dates in $ARGUMENTS). After 9 PM ET include today; before 9 PM, say today may be partial.

1. **Main login (6 stores: Wellington, West Palm Beach, Boynton Beach, Lake Worth, Plantation, Cooper City).**
   - Open `https://scenthound.mytime.com/reports` → Company → **Daily Revenue** (`/reports/revenue_time_series`). Set `start_date` and `end_date` in the URL; keep All Locations.
   - Check the location column shows the 6 stores. If it shows only PBG East and Northlake, Bryan is still on the PBG login: do step 2 first.
   - Click the green CSV icon → **Download Detailed Report**. The Downloads panel opens; click **Download** on the newest row once it says "completed". Clicking can save two copies (`… (1).csv`); use one.
2. **PBG login (PBG East, PBG Northlake).**
   - Ask Bryan to switch: account menu (top right) → **Switch User**, sign in to the PBG login, and tell you when done. Wait for his word. Never enter or ask for the password.
   - Repeat the Daily Revenue export for the same dates. Check the file has only the two PBG stores.
   - Ask Bryan to switch back to the main login.
3. **Move the files.** `mv` each new CSV from `~/Downloads` into the Revenue Analysis folder (see CLAUDE.md for the path). Add ` PBG` before `.csv` on the PBG file. `mv` keeps the modified time, which `merge_exports.py` uses for its before-9-PM check. Delete only the duplicate `(1)` copy you made, nothing else in Downloads.
4. **Skip if nothing changed.** If an export has the same rows as the last one already merged (compare with `csv.DictReader`; column order can differ), say so.
5. Follow `/update-revenue` from step 3 with these files, and report the same way.

The column order differs between the By Date and By Location views; `merge_exports.py` reads columns by name, so either is fine.
