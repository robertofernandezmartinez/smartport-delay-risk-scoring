import pandas as pd
import datetime
import hashlib
import gspread
import os
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURATION (SmartPort AI Final Clean Version) ---
CSV_SOURCE = '05_Outputs/predictions.csv'
CREDENTIALS_FILE = "credentials.json"
SPREADSHEET_ID = "1aTJLlg4YNT77v1PLQccKl8ZCADBJN0U8kncTBvf43P0"

def generate_prediction_id(vessel_id, timestamp):
    """Generates the unique audit hash (DNI of the row)"""
    unique_str = f"{vessel_id}_{timestamp}"
    return hashlib.sha256(unique_str.encode()).hexdigest()[:12]

def sync_predictions_to_cloud():
    """
    Direct Cloud Sync:
    Fires ML predictions from local CSV directly to Google Sheets.
    No redundant labels, just pure operational data.
    """
    # 1. Auth Setup
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        print("✅ Auth Success: Connected to SmartPort Cloud.")
    except Exception as e:
        print(f"❌ Auth Error: {e}")
        return

    # 2. Load ML Predictions from your execution.py output
    if not os.path.exists(CSV_SOURCE):
        print(f"❌ Error: {CSV_SOURCE} not found.")
        return

    df = pd.read_csv(CSV_SOURCE)
    existing_ids = sheet.col_values(1)
    
    # Sorting to prioritize high-risk vessels
    top_vessels = df.sort_values(by='risk_score', ascending=False).head(100)

    prepared_rows = []
    for _, row in top_vessels.iterrows():
        # Using the execution_time from your CSV to keep it 100% faithful
        exec_time = row['execution_time']
        v_id = int(row['vessel_id'])
        r_score = float(row['risk_score'])
        
        # Operational Metric: Predicted delay based on your 120min logic
        delay_min = int(r_score * 240) 
        
        p_id = generate_prediction_id(v_id, exec_time)
        
        if p_id not in existing_ids:
            # CLEAN MAPPING: A to G (7 columns)
            prepared_rows.append([
                p_id,                          # A: prediction_id
                exec_time,                     # B: timestamp_prediction
                v_id,                          # C: vessel_id
                round(r_score, 3),             # D: risk_score
                row['risk_level'],             # E: risk_level
                delay_min,                     # F: predicted_delay_minutes
                row['recommended_action'],     # G: recommended_action
                "Pending Review"               # H: status
            ])

    # 3. Final Deployment
    if prepared_rows:
        try:
            sheet.append_rows(prepared_rows)
            print(f"🚀 Deployment Success: {len(prepared_rows)} clean records synced.")
        except Exception as e:
            print(f"❌ Sync Failed: {e}")
    else:
        print("ℹ️ Everything up to date. No new records added.")

if __name__ == "__main__":
    sync_predictions_to_cloud()