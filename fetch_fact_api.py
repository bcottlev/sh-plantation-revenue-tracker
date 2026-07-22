#!/usr/bin/env python3
"""
FACT_API integration: Fetch daily revenue from Scenthound
Properly authenticated with JWT token flow
"""

import requests
import json
import re
from datetime import datetime, timedelta

# FACT_API credentials
API_ENDPOINT = "https://nhq7rwg1r6.execute-api.us-east-1.amazonaws.com/prod/"
USERNAME = "Vendor:bcottle@scenthound.com"
PASSWORD = "Password01!!!!"
PLANTATION_LOCATION_ID = "154863"  # Plantation 8126 W Broward Blvd

def get_fact_api_token():
    """Authenticate and get JWT token (valid 24 hours)"""
    try:
        response = requests.post(
            f"{API_ENDPOINT}auth",
            json={"username": USERNAME, "password": PASSWORD},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        token = data.get('token')
        if not token:
            print(f"❌ No token in response: {data}")
            return None
        print(f"✓ Got JWT token")
        return token
    except Exception as e:
        print(f"❌ Auth failed: {e}")
        return None

def fetch_revenue_data(token, location_id, start_date, end_date):
    """Fetch revenue transactions for date range"""
    headers = {
        'Authorization': token  # No "Bearer" prefix per docs
    }
    
    params = {
        'locationId': location_id,
        'startDate': start_date,
        'endDate': end_date,
        'limit': 500,
        'offset': 0
    }
    
    try:
        response = requests.get(
            f"{API_ENDPOINT}facts/revenue",
            headers=headers,
            params=params,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        print(f"✓ Fetched revenue data ({len(data.get('data', []))} transactions)")
        return data
    except Exception as e:
        print(f"❌ Fetch failed: {e}")
        return None

def calculate_mtd_from_transactions(transactions):
    """Sum net revenue from transaction list"""
    total = 0.0
    for tx in transactions:
        if tx.get('transaction_type') == 'net_revenue':
            amount = tx.get('item_amount', 0)
            total += float(amount)
    return total

def update_tracker_html(mtd_total, days_completed, month, year):
    """Update the tracker HTML with new MTD"""
    
    # Calculate projections based on month
    if month == 7:  # July
        membership = 12613.26
        target_total = 33755
        days_in_month = 31
        tracker_file = 'july/index.html'
    else:  # June or other
        membership = 11908.50
        target_total = 30984
        days_in_month = 30
        tracker_file = 'june/index.html'
    
    mtd_addons = mtd_total - membership
    addon_days = days_completed - 1
    daily_avg = (mtd_addons / addon_days) if addon_days > 0 else 0
    days_remaining = days_in_month - days_completed
    projection = mtd_total + (daily_avg * days_remaining)
    
    # Read existing tracker
    try:
        with open(tracker_file, 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Could not read {tracker_file}: {e}")
        return False
    
    # Update JavaScript variables
    old_mtd = re.search(r'const mtdTotal = [\d.]+', content)
    if old_mtd:
        content = content.replace(old_mtd.group(0), f'const mtdTotal = {mtd_total}')
    
    old_membership = re.search(r'const membership = [\d.]+', content)
    if old_membership:
        content = content.replace(old_membership.group(0), f'const membership = {membership}')
    
    # Update day range display
    old_range = re.search(r'MTD Total \(\w+ 1-\d+\)', content)
    if old_range:
        month_name = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][month]
        content = content.replace(old_range.group(0), f'MTD Total ({month_name} 1-{days_completed})')
    
    # Write back
    try:
        with open(tracker_file, 'w') as f:
            f.write(content)
        print(f"✅ Updated {tracker_file}: MTD=${mtd_total:.2f}, Projection=${projection:.0f}")
        return True
    except Exception as e:
        print(f"❌ Write failed: {e}")
        return False

def main():
    print("🔄 Fetching FACT_API revenue data...")
    
    # Today's date
    today = datetime.now()
    month = today.month
    year = today.year
    
    # Set date range: start of month to today
    start_date = f"{year}-{month:02d}-01"
    end_date = today.strftime("%Y-%m-%d")
    days_completed = today.day
    
    # Authenticate
    token = get_fact_api_token()
    if not token:
        print("❌ Authentication failed")
        return False
    
    # Fetch revenue
    data = fetch_revenue_data(token, PLANTATION_LOCATION_ID, start_date, end_date)
    if not data:
        print("❌ Data fetch failed")
        return False
    
    # Calculate MTD from transactions
    transactions = data.get('data', [])
    if not transactions:
        print("❌ No transactions returned")
        return False
    
    mtd_total = calculate_mtd_from_transactions(transactions)
    
    if mtd_total == 0:
        print("❌ MTD total is zero")
        return False
    
    print(f"✓ MTD Total: ${mtd_total:.2f}")
    
    # Update tracker
    if update_tracker_html(mtd_total, days_completed, month, year):
        print("✓ Tracker updated successfully")
        return True
    else:
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
