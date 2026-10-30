# RingCentral archive — setup

Every night `ringcentral_archive.py` (workflow **RingCentral Archive**, 4:30 AM ET) saves the
previous days' calls and texts before RingCentral deletes them (texts after ~6 weeks).

- **Raw records** (with customer phone numbers) → private Google Drive folder *RingCentral Archive*,
  one JSON file per day: `calls/YYYY-MM/YYYY-MM-DD.json`, `texts/YYYY-MM/YYYY-MM-DD.json`.
- **Daily totals per line** (counts only) → `data/ringcentral/daily.csv` in this repo.

Until the five secrets below exist, the nightly run skips without failing.

## 1. RingCentral API credential (~10 min)

1. Sign in at developers.ringcentral.com with your RingCentral admin login → **Console → Apps → Create App**.
2. **REST API App** → Next.
3. Authentication: **JWT auth flow**.
4. Security → app permissions: **Read Accounts**, **Read Call Log**, **Read Messages**.
5. Select **"This app is private and will only be callable using credentials from the same RingCentral account."** Create.
6. On the app page, copy the **production** Client ID and Client Secret (if only sandbox credentials show, use *Apply for production*).
7. Profile menu → **Credentials → Create JWT** for your user (you can restrict it to this app). Copy the JWT.

## 2. Google Drive receiver (~5 min)

1. Go to script.google.com while signed in to the Google account that should own the archive → **New project**.
2. Replace the code with `ringcentral/drive_receiver.gs`, and set `TOKEN` to a long passphrase of your choosing.
3. **Deploy → New deployment → Web app**: Execute as **Me**, Who has access **Anyone** → Deploy, approve the Drive permission.
4. Copy the **Web app URL**.

## 3. GitHub secrets

Repo → Settings → Secrets and variables → Actions → New repository secret:

| Secret | Value |
|---|---|
| `RC_CLIENT_ID` | from step 1.6 |
| `RC_CLIENT_SECRET` | from step 1.6 |
| `RC_JWT` | from step 1.7 |
| `DRIVE_WEBHOOK_URL` | Web app URL from step 2.4 |
| `DRIVE_WEBHOOK_TOKEN` | the passphrase from step 2.2 |

## 4. First run (backfill)

Actions → **RingCentral Archive** → Run workflow → `from_date` = `2026-02-01`.
That saves everything RingCentral still has (calls since opening; texts only from ~mid-September,
older ones are already gone). It takes about 30–40 minutes because the call-log API allows
10 requests a minute. After that the nightly run keeps it current.
