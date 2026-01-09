import pandas as pd
import datetime
import hashlib
import gspread
import os
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURATION ---
CSV_SOURCE = '05_Outputs/predictions.csv'
CREDENTIALS_FILE = "credentials.json"
SPREADSHEET_ID = "1aTJLlg4YNT77v1PLQccKl8ZCADBJN0U8kncTBvf43P0"

def generate_prediction_id(vessel_id, timestamp):
    """Generates a unique ID for the Google Sheets row - EXACTLY as before"""
    unique_str = f"{vessel_id}_{timestamp}"
    return hashlib.sha256(unique_str.encode()).hexdigest()[:12]

def sync_predictions_to_sheets():
    # 1. Google Sheets Setup
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1

    # 2. Load ML Predictions
    try:
        df = pd.read_csv(CSV_SOURCE)
    except FileNotFoundError:
        print(f"❌ Error: '{CSV_SOURCE}' not found.")
        return

    # 3. Process Data (Top 100 instead of Top 5 to make it "richer")
    # We sort by risk_score just like you did
    top_vessels = df.sort_values(by='risk_score', ascending=False).head(100)

    print(f"🚀 Processing {len(top_vessels)} vessels for Google Sheets...")

    new_rows = []
    for _, row in top_vessels.iterrows():
        # EXACT logic from your original script
        now_iso = datetime.datetime.utcnow().isoformat() + "Z"
        vessel_id = int(row['vessel_id'])
        
        # We recreate the payload you had for n8n
        prediction_id = generate_prediction_id(vessel_id, now_iso)
        
        new_rows.append([
            prediction_id,          # Column A: prediction_id
            now_iso,                # Column B: timestamp_prediction
            vessel_id,              # Column C: vessel_id
            round(float(row['risk_score']), 2), # Column D: risk_score
            row['risk_level'],      # Column E: risk_level
            row['recommended_action'], # Column F: recommended_action
            "Pending Review"        # Column G: status
        ])

    # 4. Bulk Upload
    if new_rows:
        sheet.append_rows(new_rows)
        print(f"✅ Success: {len(new_rows)} vessels uploaded with original logic.")
    else:
        print("ℹ️ No data to sync.")

if __name__ == "__main__":
    sync_predictions_to_sheets()