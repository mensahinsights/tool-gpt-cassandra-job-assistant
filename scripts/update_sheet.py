import os
import json
import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

def update_sheet(result_json_path: str):
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

        row = [
            datetime.date.today().isoformat(),
            result.get("company", "Unknown"),
            result.get("job_title", "Unknown"),
            result.get("closing_date", "TBD"),
            result.get("jd_url", ""),
            json.dumps(result.get("roles_processed", {}))
        ]

        body = {"values": [row]}
        service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range="job_tracker!A:F",  # 👈 must match tab name
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
