import os
import re
from datetime import datetime
from slack_sdk import WebClient

# Initialize Slack client
slack_token = os.environ.get("SLACK_BOT_TOKEN")
client = WebClient(token=slack_token)

print("🔍 Pulling historical data from Slack...")

# Read Slack channel using channel ID
channel_id = "C0B241EHPP0"
try:
    # Get all messages (need to paginate)
    all_messages = []
    cursor = None
    
    while True:
        result = client.conversations_history(channel=channel_id, limit=100, cursor=cursor)
        all_messages.extend(result["messages"])
        
        if not result.get("has_more"):
            break
        cursor = result["response_metadata"]["next_cursor"]
    
    print(f"✓ Retrieved {len(all_messages)} messages")
except Exception as e:
    print(f"❌ Error reading Slack: {e}")
    exit(1)

# Extract revenue for June 9-16
daily_revenue = {}

for msg in all_messages:
    text = msg.get("text", "")
    
    # Look for End-of-Shift reports with dates in June 9-16
    if "End-of-Shift PL SM Report" in text:
        # Extract date
        date_match = re.search(r"Date of Report:\s*(\d{4}-\d{2}-\d{2})", text)
        if date_match:
            date_str = date_match.group(1)
            # Check if it's June 9-16
            if "2026-06-" in date_str:
                day = int(date_str.split("-")[2])
                if 9 <= day <= 16:
                    # Extract Net Revenue
                    revenue_match = re.search(r"Net Revenue:\s*\$([0-9.]+)", text)
                    if revenue_match:
                        revenue = float(revenue_match.group(1))
                        daily_revenue[day] = revenue
                        print(f"✓ June {day}: ${revenue}")

print(f"\n📊 Found {len(daily_revenue)} days of data")

if not daily_revenue:
    print("⚠️ No revenue data found for June 9-16")
    exit(0)

# Read tracker
tracker_path = "june/index.html"
with open(tracker_path, 'r') as f:
    content = f.read()

# Update dailyLog in JavaScript
log_pattern = r"let dailyLog = \[(.*?)\];"
log_match = re.search(log_pattern, content, re.DOTALL)

if log_match:
    old_log = log_match.group(0)
    
    # Build new log with all existing + new entries
    new_entries = []
    for day in sorted(daily_revenue.keys()):
        new_entries.append(f"            {{ day: {day}, revenue: {daily_revenue[day]} }}")
    
    # Create new log array with comma-separated entries
    new_log = "let dailyLog = [\n" + ",\n".join(new_entries) + "\n        ];"
    
    content = content.replace(old_log, new_log)
    print(f"\n✓ Updated tracker with {len(daily_revenue)} days")

# Write tracker
with open(tracker_path, 'w') as f:
    f.write(content)

print("✓ Tracker updated locally")
print("\nNow run: git add june/index.html && git commit -m 'Backfill June 9-16 revenue' && git push origin main")

