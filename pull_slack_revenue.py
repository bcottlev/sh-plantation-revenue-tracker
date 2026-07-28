#!/usr/bin/env python3
"""
Pull daily revenue from Slack End-of-Shift PL SM Report
and update tracker
"""

import os
import re
import requests
from datetime import datetime

SLACK_API = "https://slack.com/api/conversations.history"
SLACK_CHANNEL = "C0B241EHPP0"  # plantation-leadership

def get_slack_messages(token, channel, limit=50):
    """Fetch recent messages from Slack channel"""
    headers = {'Authorization': f'Bearer {token}'}
    params = {
        'channel': channel,
        'limit': limit
    }
    
    try:
        response = requests.get(SLACK_API, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get('ok'):
            return data.get('messages', [])
        else:
            print(f"❌ Slack API error: {data.get('error')}")
            return []
    except Exception as e:
        print(f"❌ Failed to fetch Slack messages: {e}")
        return []

def parse_eom_report(message_text):
    """Parse End-of-Shift PL SM Report to extract date and revenue"""
    
    # Look for date
    date_match = re.search(r'Date of Report: (\d{4}-\d{2}-\d{2})', message_text)
    revenue_match = re.search(r'Net Revenue: \$([0-9,.]+)', message_text)
    
    if date_match and revenue_match:
        date_str = date_match.group(1)
        revenue_str = revenue_match.group(1).replace(',', '')
        revenue = float(revenue_str)
        return {'date': date_str, 'revenue': revenue}
    
    return None

def update_tracker_with_revenue(month, date, revenue):
    """Update tracker HTML with new daily revenue"""
    tracker_file = f'{month}/index.html'
    
    try:
        with open(tracker_file, 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Could not read tracker: {e}")
        return False
    
    # Extract day from date (YYYY-MM-DD)
    day = int(date.split('-')[2])
    
    # Update the JavaScript dailyData or mtdTotal
    # For now, we'll update mtdTotal directly
    mtd_match = re.search(r'const mtdTotal = ([\d.]+)', content)
    if not mtd_match:
        print("❌ Could not find mtdTotal in tracker")
        return False
    
    old_mtd = float(mtd_match.group(1))
    new_mtd = old_mtd + revenue
    
    content = content.replace(
        f'const mtdTotal = {old_mtd}',
        f'const mtdTotal = {new_mtd}'
    )
    
    # Update daysCompleted
    days_match = re.search(r'const daysCompleted = (\d+)', content)
    if days_match:
        old_days = int(days_match.group(1))
        if day > old_days:
            content = content.replace(
                f'const daysCompleted = {old_days}',
                f'const daysCompleted = {day}'
            )
    
    try:
        with open(tracker_file, 'w') as f:
            f.write(content)
        print(f"✅ Updated {tracker_file}: +${revenue:.2f} | MTD now ${new_mtd:.2f}")
        return True
    except Exception as e:
        print(f"❌ Could not write tracker: {e}")
        return False

def main():
    print("📊 Pulling revenue from Slack End-of-Shift Report...")
    
    # Get bot token
    token = os.getenv('SLACK_BOT_TOKEN')
    if not token:
        print("❌ SLACK_BOT_TOKEN not set")
        return False
    
    # Fetch messages
    messages = get_slack_messages(token, SLACK_CHANNEL, limit=30)
    if not messages:
        print("❌ No messages retrieved")
        return False
    
    # Find latest End-of-Shift PL SM Report
    latest_report = None
    for msg in messages:
        text = msg.get('text', '')
        if 'End-of-Shift PL SM Report' in text:
            latest_report = text
            break
    
    if not latest_report:
        print("⚠️  No End-of-Shift PL SM Report found")
        return False
    
    # Parse report
    data = parse_eom_report(latest_report)
    if not data:
        print("❌ Could not parse report")
        return False
    
    print(f"✓ Found report for {data['date']}: ${data['revenue']:.2f}")
    
    # Determine month
    month_num = int(data['date'].split('-')[1])
    month = 'july' if month_num == 7 else 'june'
    
    # Update tracker
    if update_tracker_with_revenue(month, data['date'], data['revenue']):
        return True
    else:
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
