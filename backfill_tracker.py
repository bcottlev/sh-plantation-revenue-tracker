import os
import re
from slack_sdk import WebClient

slack_token = os.environ.get("SLACK_BOT_TOKEN")
client = WebClient(token=slack_token)

print("🔍 Pulling historical data from Slack...")

channel_id = "C0B241EHPP0"
try:
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

daily_revenue = {}

for msg in all_messages:
    # Check for End-of-Shift report in text
    text = msg.get("text", "")
    
    if "End-of-Shift PL SM Report" in text:
        # Try to extract date and revenue from text
        date_match = re.search(r"Date of Report:\s*(\d{4}-\d{2}-\d{2})", text)
        revenue_match = re.search(r"Net Revenue:\s*\$([0-9.]+)", text)
        
        if date_match and revenue_match:
            date_str = date_match.group(1)
            revenue = float(revenue_match.group(1))
            
            # Check if it's June 9-16
            if "2026-06-" in date_str:
                day = int(date_str.split("-")[2])
                if 9 <= day <= 16:
                    daily_revenue[day] = revenue
                    print(f"✓ June {day}: ${revenue}")

print(f"\n📊 Found {len(daily_revenue)} days of data")

if not daily_revenue:
    print("⚠️  No revenue data found for June 9-16")
    exit(0)

# Read tracker
tracker_path = "june/index.html"
with open(tracker_path, 'r') as f:
    content = f.read()

# Update dailyLog - replace the entire array
log_pattern = r"let dailyLog = \[.*?\];"
match = re.search(log_pattern, content, re.DOTALL)

if match:
    # Build new entries list
    new_entries = []
    for day in sorted(daily_revenue.keys()):
        new_entries.append(f"            {{ day: {day}, revenue: {daily_revenue[day]} }}")
    
    new_log = "let dailyLog = [\n" + ",\n".join(new_entries) + "\n        ];"
    content = re.sub(log_pattern, new_log, content, flags=re.DOTALL)
    
    print(f"✓ Updated tracker with {len(daily_revenue)} days")

# Write tracker
with open(tracker_path, 'w') as f:
    f.write(content)

print("✓ Tracker updated and ready to push")

