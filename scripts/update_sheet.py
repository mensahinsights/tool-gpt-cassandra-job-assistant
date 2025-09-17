#!/usr/bin/env python3
import os, sys, json, tempfile
from google.oauth2 import service_account
from googleapiclient.discovery import build

def main():
    if len(sys.argv) != 2:
        print("Usage: update_sheet.py <result.json>")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        res = json.load(f)

    creds_json = os.environ["GOOGLE_SHEETS_CREDENTIALS"]
    sheet_id = os.environ["SHEET_ID"]

    cred_file = tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8")
    cred_file.write(creds_json)
    cred_file.flush()
    cred_file.close()

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = service_account.Credentials.from_service_account_file(cred_file.name, scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()

    row = [
        res.get("Date",""),
        res.get("Company",""),
        res.get("Job_Title",""),
        res.get("JD_Path",""),
        res.get("Closing_Date",""),
        res.get("ATS_Score","")
    ]
    body = {"values":[row]}
    sheet.values().append(spreadsheetId=sheet_id, range="Sheet1!A:F", valueInputOption="RAW", body=body).execute()
    print("Updated sheet with row:", row)

if __name__ == "__main__":
    main()
