"""
Erie Hall Court Gap Finder
===========================
Main entry point - works both locally and in GitHub Actions CI.

Usage:
    python main.py           # Run the gap finder
    python main.py --setup   # Configure secure keyring storage (local only)
"""

import sys
import os
import gc
import json
import time
from datetime import datetime, timedelta, date
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from config import COURTS
from security import get_credentials, setup_keyring
from auth import auto_login
from calendar_parser import (scrape_calendar_data, format_hour, click_next_week, parse_date)

# Detect CI environment
IS_CI = os.getenv("CI") == "true"


def save_results_json(all_gaps, all_badminton):
    """
    Save results to JSON file for API access.
    Sorts strictly by date.
    """
    output = {
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "courts": {},
        "badminton_open_play": []
    }
    
    # Helper to sort dates
    def date_key(d_str):
        return parse_date(d_str) or date.min

    # Add court gaps
    for court_name, gaps in all_gaps.items():
        court_data = []
        # Sort by date
        sorted_dates = sorted(gaps.keys(), key=date_key)
        
        for date_str in sorted_dates:
            day_gaps = gaps[date_str]
            day_data = {
                "date": date_str,
                "slots": []
            }
            for gap in day_gaps:
                day_data["slots"].append({
                    "start": format_hour(gap['start']),
                    "end": format_hour(gap['end']),
                    "duration_hours": round(gap['duration'], 1)
                })
            court_data.append(day_data)
        output["courts"][court_name] = court_data
    
    # Add badminton events - Sort by date
    all_badminton.sort(key=lambda x: x['date']) # parsed date object
    
    for event in all_badminton:
        output["badminton_open_play"].append({
            "name": event['name'],
            "date": event['date_str'],
            "start": event['start'],
            "end": event['end'],
            "court": event.get('court', 'Unknown')
        })
    
    with open("gaps.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n  Results saved to gaps.json")


def filter_for_week(data_dict, target_start_date, days=7):
    """
    Filter a dictionary of {date_str: data} to only include dates 
    within [target_start_date, target_start_date + 6 days].
    """
    filtered = {}
    target_end_date = target_start_date + timedelta(days=days-1)
    
    for date_str, content in data_dict.items():
        d = parse_date(date_str)
        if d and target_start_date <= d <= target_end_date:
            filtered[date_str] = content
            
    return filtered

def main():
    """Main application entry point"""
    
    # Handle --setup flag (local only)
    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        if IS_CI:
            print("ERROR: --setup is not available in CI mode")
            return
        setup_keyring()
        return
    
    # Minimal status output
    print("  ERIE HALL COURT GAP FINDER")
    if IS_CI:
        print("  (Running in GitHub Actions)")
    
    # Load credentials
    username, password, totp_secret = get_credentials()
    
    # Browser setup
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")  # Suppress Chrome logs
    
    if IS_CI:
        options.add_argument("--headless")
    
    if IS_CI:
        service = Service()
        driver = webdriver.Chrome(service=service, options=options)
    else:
        # Use webdriver_manager handles driver verification/installation locally
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    
    all_gaps = {}
    all_badminton = []
    
    # Define our target window: Today + 6 days
    today = datetime.now().date()
    end_date = today + timedelta(days=6)
    
    try:
        first_url = list(COURTS.values())[0]
        login_success = auto_login(driver, first_url, username, password, totp_secret)
        
        # Clear credentials
        password = '\x00' * len(password) if password else None
        totp_secret = '\x00' * len(totp_secret) if totp_secret else None
        del password, totp_secret
        gc.collect()
        
        if not login_success:
            if IS_CI:
                print("ERROR: Auto-login failed in CI mode")
                sys.exit(1)
            else:
                print("\n  AUTO-LOGIN FAILED - Please log in manually.")
                input("Press ENTER after login...")
        
        print(f"\nScanning courts ({today.strftime('%b %d')} - {end_date.strftime('%b %d')})...")

        for court_name, url in COURTS.items():
            print(f"  Checking {court_name}...")
            driver.get(url)
            time.sleep(3) # Explicit wait for page load
            
            # 1. Scrape current week
            gaps_week1, badminton_week1 = scrape_calendar_data(driver)
            
            # Robust check for Week 1 data
            if not gaps_week1 and not badminton_week1:
                # Retry once if empty
                print("    ...Retrying scrape for current week...")
                driver.refresh()
                time.sleep(5)
                gaps_week1, badminton_week1 = scrape_calendar_data(driver)
            
            # 2. Click Next and Scrape (Week 2)
            week2_success = click_next_week(driver)
            gaps_week2 = {}
            badminton_week2 = []
            
            if week2_success:
                gaps_week2, badminton_week2 = scrape_calendar_data(driver)
            
            # 3. Merge results
            merged_gaps = {**gaps_week1, **gaps_week2}
            
            # 4. Filter for [Today, Today+6]
            filtered_gaps = filter_for_week(merged_gaps, today, 7)
            all_gaps[court_name] = filtered_gaps
            
            # Merge and filter badminton
            merged_badminton = badminton_week1 + badminton_week2
            filtered_badminton = [
                e for e in merged_badminton 
                if e['date'] and today <= e['date'] <= end_date
            ]
            
            # Dedup badminton events
            seen = set()
            for e in filtered_badminton:
                key = (e['name'], e['date_str'], e['start'])
                if key not in seen:
                    seen.add(key)
                    e['court'] = court_name
                    all_badminton.extend([e])
        
        save_results_json(all_gaps, all_badminton)
        
        if not IS_CI:
            print("Scan finished.")

    finally:
        driver.quit()
        gc.collect()


if __name__ == "__main__":
    main()
