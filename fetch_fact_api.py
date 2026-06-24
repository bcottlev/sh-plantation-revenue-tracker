#!/usr/bin/env python3
"""
FACT_API integration: Fetch daily revenue from Scenthound
"""

import requests
import json
import re
from datetime import datetime, timedelta
import base64

# FACT_API credentials
API_ENDPOINT = "https://nhq7rwg1r6.execute-api.us-east-1.amazonaws.com/prod/"
USERNAME = "Vendor : bcottle@scenthound.com"  # Note: space before colon
PASSWORD = "Password01!!!!"
LOCATION = "Plantation"  # Location name in Scenthound

def get_fact_api_token():
    """Authenticate and get access token"""
    auth_string = f"{USERNAME}:{PASSWORD}"
    auth_bytes = auth_string.encode('utf-8')
    auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
    
    headers = {
        'Authorization': f'Basic {auth_b64}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(
            f"{API_ENDPOINT}auth",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return data.get('accessToken') or data.get('token')
    except Exception as e:
        print(f"❌ Auth failed: {e}")
        return None

def fetch_revenue_data(token):
    """Fetch revenue data for Plantation location"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Query for June 1-30
    query = {
        "location": LOCATION,
        "startDate": "2026-06-01",
        "endDate": "2026-06-30"
    }
    
    try:
        response = requests.get(
            f"{API_ENDPOINT}revenue",
            headers=headers,
            params=query,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Fetch failed: {e}")
        return None

def parse_revenue_data(data):
    """Extract MTD revenue from API response"""
    if not data:
        return None
    
    # FACT_API returns daily revenue
    # Sum all net revenue from June 1 onwards
    mtd_total = 0.0
    days_processed = 0
    
    try:
        # Assuming data is a list of daily records
        if isinstance(data, list):
            for record in data:
                revenue = record.get('netRevenue') or record.get('revenue') or record.get('total')
                if revenue:
                    mtd_total += float(revenue)
                    days_processed += 1
        elif isinstance(data, dict):
            # If data is nested, try to extract daily breakdown
            daily = data.get('daily') or data.get('days') or []
            for day_record in daily:
                revenue = day_record.get('netRevenue') or day_record.get('revenue')
                if revenue:
                    mtd_total += float(revenue)
                    days_processed += 1
        
        return {
            'mtd': mtd_total,
            'days': days_processed,
            'success': True
        }
    except Exception as e:
        print(f"❌ Parse failed: {e}")
        return None

def update_tracker(mtd_total, days_completed):
    """Update june/index.html with new MTD"""
    
    # Calculate projections
    membership = 11908.50
    mtd_addons = mtd_total - membership
    addon_days = days_completed - 1  # Exclude June 1
    daily_avg = mtd_addons / addon_days if addon_days > 0 else 0
    days_remaining = 30 - days_completed
    projection = mtd_total + (daily_avg * days_remaining)
    target = 30984
    
    # Read tracker template
    try:
        with open('june/index.html', 'r') as f:
            content = f.read()
    except:
        print("❌ Could not read june/index.html")
        return False
    
    # Replace values in the JavaScript section
    replacements = {
        'const mtdTotal = [0-9]+\.[0-9]+': f'const mtdTotal = {mtd_total}',
        '<span class="value mtd">\\$[0-9,]+</span>': f'<span class="value mtd">${int(mtd_total):,}</span>',
    }
    
    for pattern, replacement in replacements.items():
        content = re.sub(pattern, replacement, content)
    
    # Update the day display
    day_label = f"MTD Total (June 1-{days_completed})"
    content = re.sub(
        r'<span class="label">MTD Total \(June 1-\d+\)</span>',
        f'<span class="label">MTD Total (June 1-{days_completed})</span>',
        content
    )
    
    # Write back
    try:
        with open('june/index.html', 'w') as f:
            f.write(content)
        print(f"✅ Updated tracker: MTD=${mtd_total:.2f}, Days={days_completed}, Projection=${projection:.0f}")
        return True
    except Exception as e:
        print(f"❌ Write failed: {e}")
        return False

def main():
    print("🔄 Fetching FACT_API data...")
    
    # Authenticate
    token = get_fact_api_token()
    if not token:
        print("❌ Authentication failed")
        return False
    
    print("✓ Authenticated")
    
    # Fetch revenue
    data = fetch_revenue_data(token)
    if not data:
        print("❌ Data fetch failed")
        return False
    
    print(f"✓ Fetched {len(data) if isinstance(data, list) else 'data'}")
    
    # Parse
    result = parse_revenue_data(data)
    if not result or not result.get('success'):
        print("❌ Parse failed")
        return False
    
    # Update tracker
    mtd = result['mtd']
    days = result['days']
    
    if update_tracker(mtd, days):
        print("✓ Tracker updated successfully")
        return True
    else:
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
