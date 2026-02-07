# Configuration and constants

# Court URLs (iCal Feeds)
COURTS = {
    "Court 1": "https://25live.collegenet.com/25live/data/psu/run/rm_reservations.ics?caller=pro&space_id=6451&start_dt=-30&end_dt=+180&options=standard",
    "Court 2": "https://25live.collegenet.com/25live/data/psu/run/rm_reservations.ics?caller=pro&space_id=6452&start_dt=-30&end_dt=+180&options=standard",
    "Court 3": "https://25live.collegenet.com/25live/data/psu/run/rm_reservations.ics?caller=pro&space_id=105&start_dt=-30&end_dt=+180&options=standard",
}

# Operating hours
# Operating hours (Day of week: (Open, Close))
# Monday=0, Sunday=6
OPERATING_HOURS = {
    0: (6, 23),   # Mon: 6 AM - 11 PM
    1: (6, 23),   # Tue: 6 AM - 11 PM
    2: (6, 23),   # Wed: 6 AM - 11 PM
    3: (6, 23),   # Thu: 6 AM - 11 PM
    4: (6, 22),   # Fri: 6 AM - 10 PM
    5: (10, 22),  # Sat: 10 AM - 10 PM
    6: (12, 23),  # Sun: 12 PM - 11 PM
}

# Keyring service name for secure storage
KEYRING_SERVICE = "erie-hall-widget"
