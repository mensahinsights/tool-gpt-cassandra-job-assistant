import os
import json
import sys
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

def update_google_sheet(result_file, sheet_id):
    with open(result_file, "r", encoding="utf-8") as f:
        result = json.load(f)

    company = result.get("company", "")
    job_title = result.get("job_title", "")
    ats_score = result.get("ats_score", "")
    resume_file = os.path.basename(result.get("resume_file", ""))

    creds_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    if not creds_json:
        raise ValueError("Missing GOOGLE_SHEETS_CREDENTIALS in env")

    creds = Credentials.from_service_account_info(
        json.loads(creds_json),
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )

    service = build("sheets", "v4", credentials=creds)

    values = [[company, job_title, ats_score, resume_file]]
    body = {"values": values}

    service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range="Sheet1!A:D",
        valueInputOption="RAW",
        body=body
    ).execute()

    print(f"[INFO] Google Sheet updated: {company}, {job_title}, {ats_score}, {resume_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python update_sheet.py <result.json>")
        sys.exit(1)

    result_file = sys.argv[1]
    sheet_id = os.environ.get("SHEET_ID")
    if not sheet_id:
        raise ValueError("Missing SHEET_ID in env")

    update_google_sheet(result_file, sheet_id)
