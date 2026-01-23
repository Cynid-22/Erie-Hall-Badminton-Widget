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
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from config import COURTS
from security import get_credentials, setup_keyring
from auth import auto_login
from calendar_parser import find_gaps, print_gaps, format_hour

# Detect CI environment
IS_CI = os.getenv("CI") == "true"


def save_results_json(all_gaps):
    """Save results to JSON file for API access"""
    output = {
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "courts": {}
    }
    
    for court_name, gaps in all_gaps.items():
        court_data = []
        for date_str, day_gaps in sorted(gaps.items()):
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
    
    with open("gaps.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✓ Results saved to gaps.json")


def main():
    """Main application entry point"""
    
    # Handle --setup flag (local only)
    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        if IS_CI:
            print("ERROR: --setup is not available in CI mode")
            return
        setup_keyring()
        return
    
    print("=" * 60)
    print("  ERIE HALL COURT GAP FINDER")
    if IS_CI:
        print("  (Running in GitHub Actions)")
    print("=" * 60)
    
    # Load credentials
    username, password, totp_secret = get_credentials()
    
    # Browser setup
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Always headless in CI, optional locally
    if IS_CI:
        options.add_argument("--headless")
        print("  Running in headless mode")
    
    # CI-specific Chrome setup
    if IS_CI:
        service = Service()
        driver = webdriver.Chrome(service=service, options=options)
    else:
        driver = webdriver.Chrome(options=options)
    
    all_gaps = {}
    
    try:
        first_url = list(COURTS.values())[0]
        print(f"\nOpening: {first_url}")
        
        login_success = auto_login(driver, first_url, username, password, totp_secret)
        
        # Clear credentials from memory
        password = '\x00' * len(password) if password else None
        totp_secret = '\x00' * len(totp_secret) if totp_secret else None
        del password, totp_secret
        gc.collect()
        
        if not login_success:
            if IS_CI:
                print("ERROR: Auto-login failed in CI mode")
                sys.exit(1)
            else:
                print("\n" + "-" * 60)
                print("  AUTO-LOGIN FAILED OR NOT CONFIGURED")
                print("  Please log in manually in the browser window.")
                print("  Once you see the calendar, press ENTER to continue...")
                print("-" * 60)
                input()
        
        print("\nScanning courts for available slots...")
        print("-" * 60)

        for court_name, url in COURTS.items():
            print(f"\nChecking {court_name}...")
            driver.get(url)
            gaps = find_gaps(driver, court_name)
            all_gaps[court_name] = gaps
            print_gaps(court_name, gaps)
        
        # Save to JSON
        save_results_json(all_gaps)
        
        print("\n" + "=" * 60)
        print("  SCAN COMPLETE!")
        print("=" * 60)
        
        if not IS_CI:
            print("\nPress Enter to close browser...")
            input()

    finally:
        driver.quit()
        print("Browser closed.")
        gc.collect()


if __name__ == "__main__":
    main()
