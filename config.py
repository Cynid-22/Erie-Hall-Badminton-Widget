# Configuration and constants

# Court URLs (iCal Feeds)
COURTS = {
    "Court 1": "https://25live.collegenet.com/25live/data/psu/run/rm_reservations.ics?caller=pro&space_id=6451&start_dt=-30&end_dt=+180&options=standard",
    "Court 2": "https://25live.collegenet.com/25live/data/psu/run/rm_reservations.ics?caller=pro&space_id=6452&start_dt=-30&end_dt=+180&options=standard",
    "Court 3": "https://25live.collegenet.com/25live/data/psu/run/rm_reservations.ics?caller=pro&space_id=105&start_dt=-30&end_dt=+180&options=standard",
}

# Operating hours
OPEN_HOUR = 6   # 6 AM
CLOSE_HOUR = 23  # 11 PM

# Keyring service name for secure storage
KEYRING_SERVICE = "erie-hall-widget"
