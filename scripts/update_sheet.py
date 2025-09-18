import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

def update_sheet(result_json_path: str):
    """Append exactly 1 row into the Google Sheet, matching header order."""
    creds_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    sheet_id = os.environ.get("SHEET_ID")

    if not creds_json or not sheet_id:
        print("[WARN] Missing Google Sheets credentials or SHEET_ID. Skipping sheet update.")
        return

    try:
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        service = build("sheets", "v4", credentials=creds)

        with open(result_json_path, "r", encoding="utf-8") as f:
            result = json.load(f)

        # Build row in exact header order
        row = [
            result.get("date", ""),          # Date
            result.get("company", ""),       # Company
            result.get("job_title", ""),     # Job Title
            result.get("jd_path", ""),       # JD Path
            result.get("closing_date", ""),  # Closing Date
            result.get("jd_url", ""),        # JD URL
            result.get("ats_score", ""),     # ATS Score
        ]

        print(f"[DEBUG] Prepared row: {row}")

        body = {"values": [row]}
        service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range="Sheet1!A:G",  # exactly 7 columns
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()

        print(f"[DEBUG] Updated Google Sheet with row: {row}")

    except Exception as e:
        print(f"[ERROR] Failed to update Google Sheet: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python update_sheet.py <result.json>")
    else:
        update_sheet(sys.argv[1])
