import os
import re
import json
from datetime import datetime
from slack_sdk import WebClient

# Initialize Slack client
slack_token = os.environ.get("SLACK_BOT_TOKEN")
client = WebClient(token=slack_token)

# Get today's date
today = datetime.now().strftime("%Y-%m-%d")
today_short = datetime.now().strftime("%m/%d/%Y")

print(f"🔍 Looking for today's revenue ({today})...")

# Read Slack channel using channel ID
channel_id = "C0AK3TZ484S"
try:
    result = client.conversations_history(channel=channel_id, limit=50)
    messages = result["messages"]
    print(f"✓ Found {len(messages)} messages in plantation-leadership")
except Exception as e:
    print(f"❌ Error reading Slack: {e}")
    exit(1)

# Find today's End-of-Shift report
today_revenue = None
today_day = int(datetime.now().strftime("%d"))

for msg in messages:
    text = msg.get("text", "")
    
    # Look for the report with today's date
    if "End-of-Shift PL SM Report" in text and today in text:
        # Extract Net Revenue
        match = re.search(r"Net Revenue:\s*\$([0-9.]+)", text)
        if match:
            today_revenue = float(match.group(1))
            print(f"✓ Found today's net revenue: ${today_revenue}")
            break

if today_revenue is None:
    print(f"⚠️  No revenue found for today ({today})")
    exit(0)

# Read tracker
tracker_path = "june/index.html"
with open(tracker_path, 'r') as f:
    content = f.read()

# Update dailyLog in JavaScript
# Find the dailyLog array and update or add today's entry
log_pattern = r"let dailyLog = \[(.*?)\];"
log_match = re.search(log_pattern, content, re.DOTALL)

if log_match:
    old_log = log_match.group(0)
    
    # Check if today already exists
    today_pattern = rf"\{{\s*day:\s*{today_day},\s*revenue:\s*[0-9.]+\s*\}}"
    
    if re.search(today_pattern, old_log):
        # Replace existing entry
        new_log = re.sub(
            today_pattern,
            f"{{ day: {today_day}, revenue: {today_revenue} }}",
            old_log
        )
        print(f"✓ Updated June {today_day} to ${today_revenue}")
    else:
        # Add new entry before closing bracket
        new_log = old_log.rstrip() 
        new_log = new_log[:-2] + f",\n            {{ day: {today_day}, revenue: {today_revenue} }}\n        ];"
        print(f"✓ Added June {today_day}: ${today_revenue}")
    
    content = content.replace(old_log, new_log)

# Write tracker
with open(tracker_path, 'w') as f:
    f.write(content)

print(f"✓ Tracker updated")
print(f"📊 June {today_day}: ${today_revenue}")

