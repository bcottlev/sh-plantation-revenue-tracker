#!/usr/bin/env python3
"""Nightly RingCentral archive.

RingCentral only keeps text messages for about six weeks (and call history for a
limited time), so every night this script:

  1. pulls the full call log and SMS records for the last few days (ET),
  2. saves the raw records, one JSON file per day, to a private Google Drive
     folder through a small Apps Script receiver (customer phone numbers never
     touch this public repo), and
  3. writes daily totals per phone line to data/ringcentral/daily.csv
     (counts only, no phone numbers) for the dashboards.

Environment (GitHub Actions secrets):
  RC_CLIENT_ID, RC_CLIENT_SECRET, RC_JWT   RingCentral REST app (JWT auth flow)
  DRIVE_WEBHOOK_URL, DRIVE_WEBHOOK_TOKEN   Apps Script receiver (ringcentral/drive_receiver.gs)
Optional:
  RC_SERVER     default https://platform.ringcentral.com
  DAYS_BACK     days before today (ET) to (re)pull, default 3
  FROM_DATE     YYYY-MM-DD: backfill from this date instead (first run)
  TO_DATE       YYYY-MM-DD: last day to pull, default yesterday (ET)
  DRY_RUN=1     pull and total, but don't upload or write the CSV
"""
import base64
import csv
import datetime as dt
import json
import os
import sys
import time
from zoneinfo import ZoneInfo

import requests

ET = ZoneInfo("America/New_York")
SERVER = os.environ.get("RC_SERVER", "https://platform.ringcentral.com").rstrip("/")
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "ringcentral", "daily.csv")
FIELDS = ["date", "line", "out_desk", "out_app", "out_60s", "out_talk_min",
          "in_calls", "in_answered", "in_missed_vm", "sms_out", "sms_in"]

session = requests.Session()


# ---------------------------------------------------------------- RingCentral
def auth():
    cid, secret, jwt = (os.environ.get(k, "") for k in ("RC_CLIENT_ID", "RC_CLIENT_SECRET", "RC_JWT"))
    if not (cid and secret and jwt):
        sys.exit("Missing RC_CLIENT_ID / RC_CLIENT_SECRET / RC_JWT")
    basic = base64.b64encode(f"{cid}:{secret}".encode()).decode()
    r = session.post(f"{SERVER}/restapi/oauth/token",
                     headers={"Authorization": f"Basic {basic}"},
                     data={"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": jwt},
                     timeout=60)
    if r.status_code != 200:
        sys.exit(f"RingCentral auth failed ({r.status_code}): {r.text[:300]}")
    session.headers["Authorization"] = f"Bearer {r.json()['access_token']}"


def get(path, params=None, pause=0.0):
    """GET with retry on rate limits; `pause` spaces out calls in heavy groups."""
    for attempt in range(8):
        r = session.get(f"{SERVER}{path}", params=params, timeout=120)
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", "60") or 60)
            print(f"  rate limited, waiting {wait}s", flush=True)
            time.sleep(wait + 1)
            continue
        if r.status_code >= 500 and attempt < 7:
            time.sleep(10 * (attempt + 1))
            continue
        r.raise_for_status()
        if pause:
            time.sleep(pause)
        return r.json()
    raise RuntimeError(f"Gave up on {path}")


def paged(path, params, pause):
    out, page = [], 1
    while True:
        j = get(path, dict(params, page=page), pause)
        recs = j.get("records", [])
        out.extend(recs)
        if not recs or not (j.get("navigation") or {}).get("nextPage"):
            return out
        page += 1


def day_bounds(day):
    start = dt.datetime.combine(day, dt.time(0), ET)
    end = start + dt.timedelta(days=1)
    return start.isoformat(), end.isoformat()


# ---------------------------------------------------------------- Google Drive
def upload(path, payload):
    url, token = os.environ.get("DRIVE_WEBHOOK_URL", ""), os.environ.get("DRIVE_WEBHOOK_TOKEN", "")
    if not (url and token):
        sys.exit("Missing DRIVE_WEBHOOK_URL / DRIVE_WEBHOOK_TOKEN")
    body = json.dumps({"token": token, "path": path, "content": json.dumps(payload, separators=(",", ":"))})
    for attempt in range(5):
        try:
            r = requests.post(url, data=body, headers={"Content-Type": "application/json"},
                              timeout=180, allow_redirects=True)
            ok = r.status_code == 200 and r.json().get("ok")
            if ok:
                return
            msg = r.text[:200]
        except (requests.RequestException, ValueError) as e:
            msg = str(e)[:200]
        time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"Drive upload failed for {path}: {msg}")


# ---------------------------------------------------------------- totals
def call_line(rec, ext_names):
    """Which phone line (extension) the call belongs to."""
    side = rec.get("from") if rec.get("direction") == "Outbound" else rec.get("to")
    ext = (side or {}).get("extensionId")
    if not ext:
        for leg in rec.get("legs") or []:
            ext = (leg.get("extension") or {}).get("id")
            if ext:
                break
    return ext_names.get(str(ext), "Main number") if ext else "Main number"


def is_desk(rec, desk_ids):
    for leg in rec.get("legs") or []:
        dev = ((leg.get("from") or {}).get("device") or {}).get("id")
        if dev:
            return str(dev) in desk_ids
    return False


def totals(day, calls, sms_by_ext, ext_names, desk_ids):
    rows = {}

    def row(line):
        return rows.setdefault(line, {f: 0 for f in FIELDS[2:]})

    for c in calls:
        r = row(call_line(c, ext_names))
        dur = c.get("duration") or 0
        if c.get("direction") == "Outbound":
            r["out_desk" if is_desk(c, desk_ids) else "out_app"] += 1
            r["out_60s"] += dur >= 60
            r["out_talk_min"] += dur / 60
        else:
            r["in_calls"] += 1
            res = c.get("result")
            r["in_answered"] += res == "Accepted"
            r["in_missed_vm"] += res in ("Missed", "Voicemail")
    for ext_id, msgs in sms_by_ext.items():
        r = row(ext_names.get(ext_id, ext_id))
        for m in msgs:
            r["sms_out" if m.get("direction") == "Outbound" else "sms_in"] += 1
    out = []
    for line, r in sorted(rows.items()):
        r["out_talk_min"] = round(r["out_talk_min"])
        out.append(dict(date=day.isoformat(), line=line, **{k: int(v) for k, v in r.items()}))
    return out


def merge_csv(new_rows, days):
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    keep = []
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, newline="") as f:
            done = {d.isoformat() for d in days}
            keep = [r for r in csv.DictReader(f) if r["date"] not in done]
    allrows = sorted(keep + new_rows, key=lambda r: (r["date"], r["line"]))
    with open(CSV_PATH, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(allrows)


# ---------------------------------------------------------------- main
def main():
    keys = ("RC_CLIENT_ID", "RC_CLIENT_SECRET", "RC_JWT", "DRIVE_WEBHOOK_URL", "DRIVE_WEBHOOK_TOKEN")
    if not any(os.environ.get(k) for k in keys):
        print("RingCentral archive not configured yet (no secrets set); skipping. See ringcentral/SETUP.md")
        return
    today = dt.datetime.now(ET).date()
    last = dt.date.fromisoformat(os.environ["TO_DATE"]) if os.environ.get("TO_DATE") else today - dt.timedelta(days=1)
    if os.environ.get("FROM_DATE"):
        first = dt.date.fromisoformat(os.environ["FROM_DATE"])
    else:
        first = last - dt.timedelta(days=int(os.environ.get("DAYS_BACK", "3")) - 1)
    days = [first + dt.timedelta(days=i) for i in range((last - first).days + 1)]
    dry = os.environ.get("DRY_RUN") == "1"
    print(f"Archiving {first} to {last} ({len(days)} days){' [dry run]' if dry else ''}", flush=True)

    auth()
    exts = paged("/restapi/v1.0/account/~/extension", {"type": "User", "perPage": 1000}, 1.5)
    ext_names = {str(e["id"]): e.get("name") or e.get("extensionNumber") for e in exts}
    devices = paged("/restapi/v1.0/account/~/device", {"perPage": 1000}, 1.5)
    desk_ids = {str(d["id"]) for d in devices if d.get("type") == "HardPhone"}
    print(f"  {len(ext_names)} lines, {len(desk_ids)} desk phones", flush=True)

    all_rows = []
    for day in days:
        frm, to = day_bounds(day)
        calls = paged("/restapi/v1.0/account/~/call-log",
                      {"view": "Detailed", "type": "Voice", "dateFrom": frm, "dateTo": to, "perPage": 1000},
                      6.5)  # call log is a heavy API group (10 requests a minute)
        sms_by_ext = {}
        for ext_id in ext_names:
            msgs = paged(f"/restapi/v1.0/account/~/extension/{ext_id}/message-store",
                         {"messageType": "SMS", "dateFrom": frm, "dateTo": to, "perPage": 250}, 1.5)
            if msgs:
                sms_by_ext[ext_id] = msgs
        n_sms = sum(len(v) for v in sms_by_ext.values())
        print(f"{day}: {len(calls)} calls, {n_sms} texts", flush=True)

        if not dry:
            month = day.strftime("%Y-%m")
            pulled = dt.datetime.now(ET).isoformat(timespec="seconds")
            upload(f"calls/{month}/{day}.json", {"date": str(day), "pulled_at": pulled, "lines": ext_names, "records": calls})
            upload(f"texts/{month}/{day}.json", {"date": str(day), "pulled_at": pulled, "lines": ext_names,
                                                 "records_by_line": sms_by_ext})
        all_rows.extend(totals(day, calls, sms_by_ext, ext_names, desk_ids))

    if dry:
        for r in all_rows:
            print(r)
    else:
        merge_csv(all_rows, days)
        print(f"Wrote {len(all_rows)} rows to {CSV_PATH}")


if __name__ == "__main__":
    main()
