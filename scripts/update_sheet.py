import os
import json
import sys
from pathlib import Path
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from datetime import datetime

def update_google_sheet(results, sheet_id):
    creds_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    if not creds_json:
        raise ValueError("Missing GOOGLE_SHEETS_CREDENTIALS in env")

    creds = Credentials.from_service_account_info(
        json.loads(creds_json),
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )

    service = build("sheets", "v4", credentials=creds)

    # Read existing rows
    existing = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range="Sheet1!A:G"
    ).execute().get("values", [])

    existing_keys = set()
    for row in existing[1:]:  # skip header
        if len(row) >= 4:
            key = (row[1], row[2], row[3])  # Company, Job Title, JD Path
            existing_keys.add(key)

    values = []
    for result_file in results:
        with open(result_file, "r", encoding="utf-8") as f:
            result = json.load(f)

        key = (result.get("company", ""), result.get("job_title", ""), result.get("jd_path", ""))
        if key in existing_keys:
            print(f"[SKIP] Duplicate entry for {key}, skipping append.")
            continue

        row = [
            datetime.now().strftime("%Y-%m-%d"),   # Date
            result.get("company", ""),
            result.get("job_title", ""),
            result.get("jd_path", ""),
            result.get("closing_date", "TBD Closing Date"),
            result.get("jd_url", ""),
            result.get("ats_score", "")
        ]
        values.append(row)

    if values:
        body = {"values": values}
        service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range="Sheet1!A:G",
            valueInputOption="RAW",
            body=body
        ).execute()
        print(f"[INFO] Appended {len(values)} new rows to Google Sheet")
    else:
        print("[INFO] No new rows to append (all duplicates)")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python update_sheet.py <results_dir>")
        sys.exit(1)

    results_dir = Path(sys.argv[1])
    sheet_id = os.environ.get("SHEET_ID")
    if not sheet_id:
        raise ValueError("Missing SHEET_ID in env")

    result_files = list(results_dir.rglob("result.json"))
    if not result_files:
        print("[ERROR] No result.json files found")
        sys.exit(1)

    update_google_sheet(result_files, sheet_id)
