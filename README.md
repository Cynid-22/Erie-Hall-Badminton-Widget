# Erie Hall Court Availability Finder

A robust, automated Python script to check for badminton court availability at Penn State Behrend's Erie Hall. It scrapes the scheduling calendar, filters for availability in the next 7 days, and detects "Badminton Club Open Play" events.

## Features

- **Automated Scanning:** Checks availability for all 3 courts for "Today" + next 6 days.
- **Secure Auto-Login:** Handles Microsoft SSO with secure TOTP (MFA) support.
- **Credentials Management:** Supports OS Keyring (encrypted) and `.env` files.
- **Badminton Detection:** Specifically looks for "Badminton Club Open Play" sessions.
- **CI/CD Integrated:** Ready-to-run on GitHub Actions (headless mode) with scheduled daily runs.
- **JSON Output:** Generates `gaps.json` for integration with widgets (like KWGT) or other apps.
- **Robust Scraper:** Handles dynamic page loads and `StaleElementReferenceException` with retry logic.

## Setup & Usage

### 1. Prerequisites
- Python 3.9+
- Chrome Browser (for local execution)

### 2. Installation
```bash
pip install -r requirements.txt
```

### 3. Local Configuration (Secure Keyring)
Run the setup mode to securely store your Penn State credentials and TOTP secret in your OS keyring.
```bash
python main.py --setup
```
This is the recommended method for local use as it avoids storing plain-text passwords in files.

### 4. Running the Script
```bash
python main.py
```
The script will:
1. Launch Chrome (headless in CI, visible locally).
2. Log in using stored credentials.
3. Scrape data for the next 7 days.
4. Save availability to `gaps.json`.

### 5. Deployment (GitHub Actions)
This project is configured to run automatically on GitHub.

1. **Push** the code to your GitHub repository.
2. Go to **Settings > Secrets and variables > Actions**.
3. Add the following **Repository Secrets**:
   - `PSU_USERNAME`: Your Penn State email.
   - `PSU_PASSWORD`: Your password.
   - `TOTP_SECRET`: The base32 secret key for your MFA (extract this when setting up Microsoft Authenticator).

The workflow `.github/workflows/check-courts.yml` runs daily at 8:00 AM EST. Results are saved or printed (custom integration required to push `gaps.json` back to repo or upload as artifact, default behavior currently verifies execution).

## File Structure

- `main.py`: Entry point. Orchestrates login, scraping, and saving.
- `calendar_parser.py`: Logic for parsing the calendar grid and handling dynamic elements.
- `security.py`: Handles credential encryption and TOTP generation.
- `auth.py`: Microsoft SSO login automation.
- `config.py`: URLs and constants.
- `gaps.json`: Output file.

## Output Format (`gaps.json`)

```json
{
  "last_updated": "2023-10-27T10:00:00Z",
  "courts": {
    "Court 1": [
      {
        "date": "2023-10-27",
        "slots": [
            { "start": "06:00 PM", "end": "08:00 PM", "duration_hours": 2.0 }
        ]
      }
    ]
  },
  "badminton_open_play": []
}
```
