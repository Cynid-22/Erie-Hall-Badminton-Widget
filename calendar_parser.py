"""
Calendar parsing module for finding available time slots.
"""

import re
import time
from selenium.webdriver.common.by import By
from config import OPEN_HOUR, CLOSE_HOUR

__all__ = ['find_gaps', 'print_gaps', 'format_hour', 'parse_time']


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


def find_gaps(driver, court_name):
    """
    Parse the 25Live calendar and find available time slots.
    Returns a dict with dates as keys and list of gaps as values.
    """
    print("  Waiting for calendar to load...")
    time.sleep(5)
    
    items = driver.find_elements(By.CSS_SELECTOR, ".grid--item")
    print(f"  Found {len(items)} calendar items")
    
    events_by_day = {}
    
    for item in items:
        aria_label = item.get_attribute("aria-label")
        if not aria_label:
            continue
            
        match = re.search(r'(\w+ \w+ \d+ \d+) from (\d+:?\d*[AP]M) until (\d+:?\d*[AP]M)', aria_label)
        if match:
            date_str = match.group(1)
            start_hour = parse_time(match.group(2))
            end_hour = parse_time(match.group(3))
            
            if start_hour is not None and end_hour is not None:
                if date_str not in events_by_day:
                    events_by_day[date_str] = []
                events_by_day[date_str].append({'start': start_hour, 'end': end_hour})
    
    # Calculate gaps
    gaps = {}
    for date_str, events in sorted(events_by_day.items()):
        events.sort(key=lambda x: x['start'])
        day_gaps = []
        current_time = OPEN_HOUR
        
        for event in events:
            if event['start'] > current_time:
                duration = event['start'] - current_time
                if duration >= 1:  # Only gaps of 1+ hours
                    day_gaps.append({
                        'start': current_time, 
                        'end': event['start'], 
                        'duration': duration
                    })
            if event['end'] > current_time:
                current_time = event['end']
        
        # Gap at end of day
        if current_time < CLOSE_HOUR:
            duration = CLOSE_HOUR - current_time
            if duration >= 1:
                day_gaps.append({
                    'start': current_time, 
                    'end': CLOSE_HOUR, 
                    'duration': duration
                })
        
        gaps[date_str] = day_gaps
    
    return gaps


def print_gaps(court_name, gaps):
    """Pretty print the available time slots"""
    print(f"\n{'='*60}")
    print(f"  AVAILABLE SLOTS: {court_name}")
    print(f"{'='*60}")
    
    if not gaps:
        print("  No schedule data found")
        return
    
    total = 0
    for date_str, day_gaps in sorted(gaps.items()):
        if day_gaps:
            print(f"\n  {date_str}:")
            for gap in day_gaps:
                start = format_hour(gap['start'])
                end = format_hour(gap['end'])
                print(f"    ✓ {start} - {end} ({gap['duration']:.1f} hrs)")
                total += 1
        else:
            print(f"\n  {date_str}: Fully booked")
    
    print(f"\n  Total available slots: {total}")
