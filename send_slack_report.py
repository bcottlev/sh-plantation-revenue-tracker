#!/usr/bin/env python3
"""
Daily revenue report to Slack with MTD, projections, and targets
"""

import requests
import json
import re
from datetime import datetime

SLACK_API = "https://slack.com/api/chat.postMessage"
SLACK_CHANNEL = "C0B241EHPP0"  # plantation-leadership

def read_tracker_data(month):
    """Extract MTD and calculations from tracker HTML"""
    tracker_file = f'{month}/index.html'
    try:
        with open(tracker_file, 'r') as f:
            content = f.read()
    except:
        return None
    
    # Extract JavaScript variables
    mtd_match = re.search(r'const mtdTotal = ([\d.]+)', content)
    membership_match = re.search(r'const membership = ([\d.]+)', content)
    target_match = re.search(r'const targetTotal = ([\d.]+)', content)
    days_completed_match = re.search(r'const daysCompleted = (\d+)', content)
    
    if not all([mtd_match, membership_match, target_match, days_completed_match]):
        return None
    
    mtd = float(mtd_match.group(1))
    membership = float(membership_match.group(1))
    target = float(target_match.group(1))
    days_completed = int(days_completed_match.group(1))
    days_in_month = 31 if month == 'july' else 30
    days_remaining = days_in_month - days_completed
    
    # Calculate metrics
    addon_revenue = mtd - membership
    addon_days = days_completed - 1
    current_daily_avg = addon_revenue / addon_days if addon_days > 0 else 0
    projection = mtd + (current_daily_avg * days_remaining)
    
    return {
        'mtd': mtd,
        'days_completed': days_completed,
        'days_remaining': days_remaining,
        'current_daily_avg': current_daily_avg,
        'projection': projection,
        'target': target,
    }

def calculate_daily_needed(mtd, days_remaining, target_amount):
    """Calculate daily average needed to hit target"""
    gap = target_amount - mtd
    if days_remaining > 0:
        return gap / days_remaining
    return 0

def format_slack_message(data, month):
    """Format message for Slack"""
    month_name = 'July' if month == 'july' else 'June'
    
    # Calculate daily needed for each tier
    targets = [30000, 31000, 32000, 33000]
    target_lines = []
    for tier in targets:
        daily = calculate_daily_needed(data['mtd'], data['days_remaining'], tier)
        target_lines.append(f"  ${tier:,}: ${daily:.0f}/day")
    
    message = f"""📊 *{month_name} Revenue Status*

*Where We Stand:*
• MTD: ${data['mtd']:,.0f}
• Days Complete: {data['days_completed']} | Days Remaining: {data['days_remaining']}

*Performance:*
• Current Daily Avg: ${data['current_daily_avg']:.0f}/day
• Projected Close: ${data['projection']:,.0f}
• Target: ${data['target']:,.0f}

*Daily Average Needed to Hit:*
{chr(10).join(target_lines)}"""
    
    return message

def send_slack_message(token, channel, message):
    """Send message to Slack"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'channel': channel,
        'text': message,
        'mrkdwn': True
    }
    
    try:
        response = requests.post(SLACK_API, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        print("✅ Message sent to Slack")
        return True
    except Exception as e:
        print(f"❌ Slack send failed: {e}")
        return False

def main():
    print("📊 Generating daily revenue report...")
    
    # Get current month
    month_num = datetime.now().month
    month = 'july' if month_num == 7 else 'june'
    
    # Read tracker data
    data = read_tracker_data(month)
    if not data:
        print("❌ Could not read tracker data")
        return False
    
    # Format message
    message = format_slack_message(data, month)
    print(f"\n{message}\n")
    
    # Get token from environment (GitHub secret)
    import os
    token = os.getenv('SLACK_BOT_TOKEN')
    if not token:
        print("❌ SLACK_BOT_TOKEN not set")
        return False
    
    # Send to Slack
    if send_slack_message(token, SLACK_CHANNEL, message):
        return True
    else:
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
