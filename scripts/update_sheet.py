import os
import json
from pathlib import Path
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

def find_latest_result_json():
    """Find the most recently created result.json file based on folder date."""
    runs_dir = Path("runs")
    if not runs_dir.exists():
        print("[ERROR] No runs directory found")
        return None
    
    # Find all result.json files
    result_files = list(runs_dir.glob("*/outputs/result.json"))
    if not result_files:
        print("[ERROR] No result.json files found")
        return None
    
    print(f"[DEBUG] Found {len(result_files)} result.json files:")
    for f in result_files:
        print(f"  - {f}")
    
    # Sort by folder name (which contains date), newest first
    # Folder format: YYYY-MM-DD_Company_JobTitle
    latest_file = max(result_files, key=lambda f: f.parent.parent.name)
    print(f"[DEBUG] Latest by folder name: {latest_file}")
    return latest_file

def update_sheet(result_json_path: str = None):
    """Append exactly 1 row into the Google Sheet, matching header order."""
    creds_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    sheet_id = os.environ.get("SHEET_ID")

    if not creds_json or not sheet_id:
        print("[WARN] Missing Google Sheets credentials or SHEET_ID. Skipping sheet update.")
        return

    # If no path provided, find the latest one
    if not result_json_path:
        latest_file = find_latest_result_json()
        if not latest_file:
            return
        result_json_path = str(latest_file)
    elif not Path(result_json_path).exists():
        print(f"[ERROR] File not found: {result_json_path}")
        latest_file = find_latest_result_json()
        if not latest_file:
            return
        result_json_path = str(latest_file)
        print(f"[DEBUG] Using latest file instead: {result_json_path}")

    try:
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        service = build("sheets", "v4", credentials=creds)

        with open(result_json_path, "r", encoding="utf-8") as f:
            result = json.load(f)

        print(f"[DEBUG] Loaded result data: {result}")

        # Strict 7-column row, always in the right order
        row = [
            result.get("date", ""),          # Date
            result.get("company", ""),       # Company
            result.get("job_title", ""),     # Job Title
            result.get("jd_path", ""),       # JD Path
            result.get("closing_date", ""),  # Closing Date
            result.get("jd_url", ""),        # JD URL
            result.get("ats_score", ""),     # ATS Score
        ]

        print(f"[DEBUG] Prepared row (length={len(row)}): {row}")

        # Verify row has exactly 7 columns
        if len(row) != 7:
            print(f"[ERROR] Row has {len(row)} columns, expected 7")
            return

        body = {"values": [row]}
        service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range="Sheet1!A:G",  # 7 fixed columns
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()

        print(f"[SUCCESS] Updated Google Sheet with row: {row}")

    except Exception as e:
        print(f"[ERROR] Failed to update Google Sheet: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Using latest result.json file...")
        update_sheet()
    else:
        update_sheet(sys.argv[1])