#!/usr/bin/env python3
"""Send daily revenue report to Slack"""
import re
import subprocess
import json
import os

print("Working directory:", os.getcwd())

# Read tracker
tracker_path = 'july/index.html'
try:
    with open(tracker_path, 'r') as f:
        content = f.read()
    print("✓ File read successfully")
except Exception as e:
    print(f"❌ Could not read {tracker_path}: {e}")
    exit(1)

# Extract values
mtd_match = re.search(r'const mtdTotal = ([\d.]+)', content)
days_match = re.search(r'const daysCompleted = (\d+)', content)
target_match = re.search(r'const targetTotal = ([\d.]+)', content)

if not all([mtd_match, days_match, target_match]):
    print("❌ Could not parse tracker variables")
    exit(1)

mtd = float(mtd_match.group(1))
days = int(days_match.group(1))
target = float(target_match.group(1))

days_remaining = 31 - days
daily_avg = (mtd - 12613.26) / (days - 1) if days > 1 else 0
projection = mtd + (daily_avg * days_remaining)

# Build message
message = f"""📊 *July Revenue Status*

*Where We Stand:*
• MTD: ${mtd:,.0f}
• Days Complete: {days} | Days Remaining: {days_remaining}

*Performance:*
• Current Daily Avg: ${daily_avg:.0f}/day
• Projected Close: ${projection:,.0f}
• Target: ${target:,.0f}

*Daily Average Needed to Hit:*
  $300/day → ${(300 * days_remaining) + mtd:,.0f}
  $600/day → ${(600 * days_remaining) + mtd:,.0f}
  $900/day → ${(900 * days_remaining) + mtd:,.0f}"""

print("\nMessage generated:")
print(message)

# Send via webhook
webhook_url = os.getenv('SLACK_WEBHOOK_URL')
if not webhook_url:
    print("❌ SLACK_WEBHOOK_URL not set")
    exit(1)

payload = json.dumps({"text": message})

cmd = ['curl', '-X', 'POST', '-H', 'Content-type: application/json', '--data', payload, webhook_url]
result = subprocess.run(cmd, capture_output=True, text=True)

print(f"\nCurl exit code: {result.returncode}")
print(f"Response: {result.stdout}")
if result.stderr:
    print(f"Stderr: {result.stderr}")

if result.returncode == 0:
    print("✅ Message sent to Slack")
    exit(0)
else:
    print("❌ Failed to send to Slack")
    exit(1)
