#!/usr/bin/env python3
import os, sys, json, tempfile
from google.oauth2 import service_account
from googleapiclient.discovery import build

def main():
    if len(sys.argv) != 2:
        print("Usage: update_sheet.py <result.json>")
        sys.exit(1)

    result_file = sys.argv[1]
    print(f"[DEBUG] Reading results from {result_file}")

    try:
        with open(result_file, "r", encoding="utf-8") as f:
            res = json.load(f)
    except Exception as e:
        print(f"[ERROR] Could not load {result_file}: {e}")
        sys.exit(1)

    if res.get("status") != "success":
        print(f"[WARNING] Skipping Google Sheet update because status={res.get('status')}")
        print(json.dumps(res, indent=2))
        sys.exit(0)

    creds_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    sheet_id = os.environ.get("SHEET_ID")

    if not creds_json or not sheet_id:
        print("[ERROR] Missing Google Sheets credentials or sheet ID")
        sys.exit(1)

    # Write creds to temp file
    cred_file = tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8")
    cred_file.write(creds_json)
    cred_file.flush()
    cred_file.close()

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = service_account.Credentials.from_service_account_file(cred_file.name, scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()

    row = [
        res.get("Date", ""),
        res.get("Company", ""),
        res.get("Job_Title", ""),
        res.get("JD_Path", ""),
        res.get("Closing_Date", ""),
        res.get("ATS_Score", "")
    ]
    body = {"values": [row]}

    try:
        sheet.values().append(
            spreadsheetId=sheet_id,
            range="Sheet1!A:F",
            valueInputOption="RAW",
            body=body
        ).execute()
        print("[DEBUG] Updated sheet with row:", row)
    except Exception as e:
        print(f"[ERROR] Failed to update Google Sheet: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
