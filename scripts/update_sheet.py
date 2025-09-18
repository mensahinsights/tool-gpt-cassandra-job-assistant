import os
import json
import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

def update_sheet(result_json_path: str):
    """Append a single row from result.json into the Google Sheet."""
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

        # Load the result.json
        with open(result_json_path, "r", encoding="utf-8") as f:
            result = json.load(f)

        # Build row in the correct column order
        row = [
            datetime.date.today().isoformat(),               # Date
            result.get("company", "Unknown Company"),        # Company
            result.get("job_title", "Unknown Role"),         # Job Title
            result.get("jd_path", ""),                       # JD Path
            result.get("closing_date", "TBD Closing Date"),  # Closing Date
            result.get("jd_url", ""),                        # JD URL
            result.get("ats_score", "fallback")              # ATS Score
        ]

        print(f"[DEBUG] Prepared row (matches header): {row}")

        # Append row into Sheet1
        body = {"values": [row]}
        service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range="Sheet1!A:G",  # 7 columns
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
