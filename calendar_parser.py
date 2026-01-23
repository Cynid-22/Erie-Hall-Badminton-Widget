"""
Calendar parsing module for finding available time slots.
"""

import re
import time
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from config import OPEN_HOUR, CLOSE_HOUR

__all__ = ['scrape_calendar_data', 'print_gaps', 'print_badminton', 'format_hour', 'click_next_week', 'parse_date']


def parse_time(time_str):
    """Convert time string like '9:05AM' to hour as float"""
    time_str = time_str.strip().upper()
    try:
        if ':' in time_str:
            match = re.match(r'(\d+):(\d+)(AM|PM)', time_str)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2))
                period = match.group(3)
                if period == 'PM' and hour != 12:
                    hour += 12
                elif period == 'AM' and hour == 12:
                    hour = 0
                return hour + minute / 60
        else:
            match = re.match(r'(\d+)(AM|PM)', time_str)
            if match:
                hour = int(match.group(1))
                period = match.group(2)
                if period == 'PM' and hour != 12:
                    hour += 12
                elif period == 'AM' and hour == 12:
                    hour = 0
                return float(hour)
    except:
        pass
    return None


def parse_date(date_str):
    """Convert date string like 'Mon Jan 19 2026' to datetime date object"""
    try:
        clean_str = date_str.replace(',', '')
        return datetime.strptime(clean_str, "%a %b %d %Y").date()
    except ValueError:
        return None


def format_hour(hour):
    """Convert hour float to readable time string"""
    h = int(hour)
    m = int((hour - h) * 60)
    period = 'AM' if h < 12 else 'PM'
    if h > 12:
        h -= 12
    elif h == 0:
        h = 12
    return f"{h}:{m:02d}{period}" if m > 0 else f"{h}{period}"


def click_next_week(driver):
    """Click the 'Next' arrow to go to the next week"""
    print("  Navigating to next week...")
    try:
        selectors = [
            "button.nav-next", 
            ".fc-next-button",
            "button[aria-label='Next Week']",
            "button[aria-label='Next period']",
            "button[aria-label='Next']",
            ".fa-chevron-right",
            ".fa-arrow-right",
            ".date-nav button:last-child",
            ".grid--header button:last-of-type"
        ]
        
        for selector in selectors:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, selector)
                if btn.is_displayed():
                    btn.click()
                    time.sleep(3)
                    return True
            except:
                continue

        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            aria = btn.get_attribute("aria-label") or ""
            if "next" in aria.lower() or "forward" in aria.lower():
                 btn.click()
                 time.sleep(3)
                 return True
                 
        print("  Could not find 'Next' button")
        return False
    except Exception as e:
        print(f"  Error clicking next: {e}")
        return False


def scrape_calendar_data(driver):
    """
    Scrape the 25Live calendar for BOTH availability gaps and badminton events in one pass.
    Returns (gaps_dict, badminton_list).
    """
    # Wait for grid
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".grid--item"))
        )
    except:
        print("  (Calendar items not found)")
        return {}, []

    # Retry loop for stale elements
    max_retries = 3
    for attempt in range(max_retries):
        try:
            items = driver.find_elements(By.CSS_SELECTOR, ".grid--item")
            
            events_by_day = {}
            badminton_events = []
            
            for item in items:
                # This get_attribute call is where StaleElementReferenceException often happens
                aria_label = item.get_attribute("aria-label")
                if not aria_label:
                    continue
                
                # --- 1. Parse Event Time for Availability ---
                match = re.search(r'(\w+ \w+ \d+ \d+) from (\d+:?\d*[AP]M) until (\d+:?\d*[AP]M)', aria_label)
                if match:
                    date_str = match.group(1)
                    start_hour = parse_time(match.group(2))
                    end_hour = parse_time(match.group(3))
                    
                    if start_hour is not None and end_hour is not None:
                        if date_str not in events_by_day:
                            events_by_day[date_str] = []
                        events_by_day[date_str].append({'start': start_hour, 'end': end_hour})

                # --- 2. Check for Badminton ---
                if 'badminton' in aria_label.lower() and match:
                    date_str = match.group(1)
                    start_time = match.group(2)
                    end_time = match.group(3)
                    date_obj = parse_date(date_str)
                    
                    name_match = re.match(r'^([^,]+)', aria_label)
                    event_name = name_match.group(1).strip() if name_match else "Badminton"
                    
                    badminton_events.append({
                        'name': event_name,
                        'date_str': date_str,
                        'date': date_obj,
                        'start': start_time,
                        'end': end_time,
                    })

            # If we completed the loop without error, calculate gaps and return
            # Gap Calculation Logic
            gaps = {}
            for date_str, events in sorted(events_by_day.items()):
                events.sort(key=lambda x: x['start'])
                day_gaps = []
                current_time = OPEN_HOUR
                
                for event in events:
                    if event['start'] > current_time:
                        duration = event['start'] - current_time
                        if duration >= 1:
                            day_gaps.append({
                                'start': current_time, 
                                'end': event['start'], 
                                'duration': duration
                            })
                    if event['end'] > current_time:
                        current_time = event['end']
                
                if current_time < CLOSE_HOUR:
                    duration = CLOSE_HOUR - current_time
                    if duration >= 1:
                        day_gaps.append({
                            'start': current_time, 
                            'end': CLOSE_HOUR, 
                            'duration': duration
                        })
                
                gaps[date_str] = day_gaps
                
            return gaps, badminton_events
            
        except StaleElementReferenceException:
            print(f"  Stale element detected, retrying scan (attempt {attempt+1}/{max_retries})...")
            time.sleep(1)
            continue
            
    print("  Failed to scan items due to stale elements.")
    return {}, []



def print_badminton(badminton_events):
    """Pretty print badminton events"""
    if not badminton_events:
        return
    
    print(f"\n{'='*60}")
    print("  BADMINTON OPEN PLAY TIMES")
    print(f"{'='*60}")
    
    by_date = {}
    for event in badminton_events:
        date_str = event['date_str']
        if date_str not in by_date:
            by_date[date_str] = []
        by_date[date_str].append(event)
    
    # Sort dates
    sorted_dates = sorted(by_date.keys(), key=lambda d: parse_date(d) or datetime.min.date())
    
    for date_str in sorted_dates:
        print(f"\n  {date_str}:")
        for event in by_date[date_str]:
            print(f"    - {event['start']} - {event['end']} ({event['name']})")


def print_gaps(court_name, gaps):
    """Pretty print the available time slots"""
    print(f"\n{'='*60}")
    print(f"  AVAILABLE SLOTS: {court_name}")
    print(f"{'='*60}")
    
    if not gaps:
        print("  No schedule data found")
        return
    
    total = 0
    # Sort dates
    sorted_dates = sorted(gaps.keys(), key=lambda d: parse_date(d) or datetime.min.date())

    for date_str in sorted_dates:
        day_gaps = gaps[date_str]
        if day_gaps:
            print(f"\n  {date_str}:")
            for gap in day_gaps:
                start = format_hour(gap['start'])
                end = format_hour(gap['end'])
                print(f"    - {start} - {end} ({gap['duration']:.1f} hrs)")
                total += 1
        else:
            print(f"\n  {date_str}: Fully booked")
    
    print(f"\n  Total available slots: {total}")

