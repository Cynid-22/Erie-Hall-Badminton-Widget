# Erie Hall Court Availability Finder

A robust, automated Python script to check for badminton court availability at Penn State Behrend's Erie Hall. It consumes the official 25Live iCal feeds to filter for availability in the next 7 days and detects "Badminton Club Open Play" events.

## Features

- **Automated Scanning:** Checks availability for all 3 courts for "Today" + next 6 days.
- **Fast & Lightweight:** Uses direct iCal feed parsing (requests + ics) instead of slow browser automation.
- **No Credentials Required:** Works without logging in or managing secrets.
- **Badminton Detection:** Specifically looks for "Badminton Club Open Play" sessions.
- **CI/CD Integrated:** Ready-to-run on GitHub Actions with scheduled daily runs.
- **JSON Output:** Generates `gaps.json` for integration with widgets (like KWGT) or other apps.

## Setup & Usage

### 1. Prerequisites
- Python 3.9+

### 2. Installation
```bash
pip install -r requirements.txt
```

### 3. Running the Script
```bash
python main.py
```
The script will:
1. Fetch calendar data from the configured iCal URLs.
2. Filter for the next 7 days.
3. Save availability and badminton sessions to `gaps.json`.

### 4. Deployment (GitHub Actions)
This project is configured to run automatically on GitHub.

The workflow `.github/workflows/check-courts.yml` runs daily at 8:05 AM EST. Results are saved to `gaps.json` and pushed back to the repository.

## File Structure

- `main.py`: Entry point. Orchestrates fetching, parsing, and saving.
- `ical_parser.py`: Logic for parsing the iCal feed and calculating gaps.
- `config.py`: iCal URLs and structure constants.
- `gaps.json`: Output file.

## Output Format (`gaps.json`)

```json
{
  "last_updated": 1700000000,
  "courts": {
    "Court 1": [
      {
        "date": "Tue, 27-Jan",
        "slots": [
            { 
              "start": "18:00", 
              "end": "20:00", 
              "duration_hours": 2.0, 
              "note": "Open" 
            }
        ]
      }
    ]
  }
}
```
