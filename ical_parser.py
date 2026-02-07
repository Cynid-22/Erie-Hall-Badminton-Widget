"""
Parser for fetching schedule data from 25Live iCal feeds.
Replaces the Selenium scraper for faster, safer access.
"""

import requests
import re
from ics import Calendar
from datetime import datetime, timedelta
import pytz
from config import OPEN_HOUR, CLOSE_HOUR

# PSU usually operates on Eastern Time
EASTERN = pytz.timezone("America/New_York")


def get_arrow_or_datetime_in_eastern(dt_obj):
    """
    Helper to convert either Arrow object (old ics) or datetime (new ics)
    to a datetime object in Eastern time.
    """
    if dt_obj is None:
        return None
        
    # If it's an Arrow object
    if hasattr(dt_obj, 'to'):
        return dt_obj.to('US/Eastern').datetime
    
    # If it's a datetime object
    if isinstance(dt_obj, datetime):
        if dt_obj.tzinfo is None:
            # Assume UTC if naive, though ics usually provides awareness
            dt_obj = pytz.utc.localize(dt_obj)
        return dt_obj.astimezone(EASTERN)
        
    return None


def fetch_ical_data(ical_url):
    """
    Fetch and parse the iCal feed.
    Returns (gaps_dict, badminton_list).
    """
    print(f"  Fetching iCal feed...")
    try:
        response = requests.get(ical_url)
        response.raise_for_status()
        c = Calendar(response.text)
    except Exception as e:
        print(f"  Error fetching iCal data: {e}")
        return {}, []

    # Get today's date to filter out old events if needed
    now = datetime.now(EASTERN)
    today = now.date()

    events_by_day = {}
    badminton_events = []

    # Iterate through all events in the calendar
    for event in c.events:
        start_dt = get_arrow_or_datetime_in_eastern(event.begin)
        end_dt = get_arrow_or_datetime_in_eastern(event.end)
        
        if not start_dt or not end_dt:
            continue
            
        # Skip past events (before today)
        if start_dt.date() < today:
            continue

        date_str = start_dt.strftime('%a %b %d %Y')  # e.g. "Mon Jan 19 2026"
        
        # Calculate float hours for existing logic
        start_hour = start_dt.hour + (start_dt.minute / 60.0)
        end_hour = end_dt.hour + (end_dt.minute / 60.0)

        # -- Store for Gap Calculation --
        if date_str not in events_by_day:
            events_by_day[date_str] = []
        
        events_by_day[date_str].append({
            'start': start_hour,
            'end': end_hour
        })

        # -- Check for Badminton --
        # 25Live event titles often contain the event name
        if event.name and 'badminton' in event.name.lower():
            badminton_events.append({
                'name': event.name,
                'date_str': date_str,
                'date': start_dt.date(),
                # Use %I:%M%p (e.g. 09:30AM) to match parse_time regex
                'start': start_dt.strftime('%I:%M%p').lstrip('0'), 
                'end': end_dt.strftime('%I:%M%p').lstrip('0'),
            })

    # Calculate Gaps (Free Time)
    gaps = {}
    
    # We need to sort by date for consistency
    sorted_date_strs = sorted(events_by_day.keys(), key=lambda d: datetime.strptime(d, "%a %b %d %Y"))
    
    for date_str in sorted_date_strs:
        events = events_by_day[date_str]
        # Sort events by start time
        events.sort(key=lambda x: x['start'])
        
        day_gaps = []
        current_time = OPEN_HOUR
        
        for event in events:
            # If there is space between current_time and event start
            if event['start'] > current_time:
                duration = event['start'] - current_time
                # Only include gaps >= 1 hour
                if duration >= 1.0:
                    day_gaps.append({
                        'start': current_time, 
                        'end': event['start'], 
                        'duration': duration
                    })
            
            # Move current_time pointer if this event extends past it
            if event['end'] > current_time:
                current_time = event['end']
        
        # Check for gap at end of day
        if current_time < CLOSE_HOUR:
            duration = CLOSE_HOUR - current_time
            if duration >= 1.0:
                day_gaps.append({
                    'start': current_time, 
                    'end': CLOSE_HOUR, 
                    'duration': duration
                })
        
        if day_gaps:
            gaps[date_str] = day_gaps

    return gaps, badminton_events


def parse_time(time_str):
    """Convert time string like '9:05AM' to hour as float"""
    if not time_str:
        return None
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
                return hour + minute / 60.0
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
    return f"{h:02d}:{m:02d}"

