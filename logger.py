import os

# ✅ Write credentials.json from Railway environment variable
google_creds = os.getenv("GOOGLE_CREDENTIALS")

if google_creds:
    decoded_creds = google_creds.replace("\\n", "\n")  # decode escaped newlines
    with open("credentials.json", "w") as f:
        f.write(decoded_creds)
else:
    raise Exception("GOOGLE_CREDENTIALS environment variable not found")

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import Set, List, Dict, Any
import time

class GoogleSheetManager:
    """Handles all interactions with the Google Sheet."""
    def __init__(self, sheet_id: str):
        try:
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive.file",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
            client = gspread.authorize(creds)

            spreadsheet = client.open_by_key(sheet_id)
            self.log_sheet = spreadsheet.worksheet("Log")
            self.processed_sheet = spreadsheet.worksheet("Processed Leads")
            self.invalid_sheet = spreadsheet.worksheet("Invalid Leads")
            print("✅ Successfully connected to Google Sheets.")
        except Exception as e:
            raise Exception(f"Failed to initialize GoogleSheetManager: {e}")

    def get_processed_emails(self) -> Set[str]:
        """Retrieves all emails from the 'Processed Leads' sheet for deduplication."""
        try:
            print("Fetching previously processed emails for deduplication...")
            emails = self.processed_sheet.col_values(1)[1:]  # Skip header
            print(f"Found {len(emails)} previously processed emails.")
            return set(emails)
        except Exception as e:
            print(f"⚠️ Warning: Could not fetch processed emails. Deduplication may not work. Error: {e}")
            return set()

    def log_run_summary(self, status: str, counts: Dict[str, Any], error_msg: str = ""):
        """Logs a summary of the automation run to the 'Log' sheet."""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        row = [
            timestamp,
            status,
            counts.get('fetched', 0),
            counts.get('new', 0),
            counts.get('verified', 0),
            counts.get('uploaded', 0),
            counts.get('deleted', 0),
            error_msg
        ]
        self.log_sheet.append_row(row)

    def log_processed_leads(self, leads: List[Dict[str, Any]]):
        """Logs successfully processed leads to the 'Processed Leads' sheet."""
        if not leads:
            return
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        rows = []
        for lead in leads:
            rows.append([
                lead['email'],
                lead.get('first_name', ''),
                lead.get('last_name', ''),
                lead.get('company', ''),
                lead.get('linkedin', ''),
                timestamp
            ])
        self.processed_sheet.append_rows(rows)
        print(f"📋 Logged {len(rows)} new leads to the 'Processed Leads' sheet.")

    def log_invalid_leads(self, leads: List[Dict[str, Any]]):
        """Logs invalid/undeliverable leads to the 'Invalid Leads' sheet."""
        if not leads:
            return
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        rows = []
        for lead in leads:
            rows.append([lead['email'], lead.get('reason', 'failed verification'), timestamp])
        self.invalid_sheet.append_rows(rows)
        print(f"🚫 Logged {len(rows)} invalid leads to the 'Invalid Leads' sheet.")
