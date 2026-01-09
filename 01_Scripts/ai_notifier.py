import pandas as pd
import datetime
import hashlib
import gspread
import os
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURATION ---
PREDICTIONS_CSV = '05_Outputs/predictions.csv'
CREDENTIALS_FILE = "credentials.json"
# Your verified Spreadsheet ID
SPREADSHEET_ID = "1aTJLlg4YNT77v1PLQccKl8ZCADBJN0U8kncTBvf43P0"

def generate_prediction_id(vessel_id, timestamp):
    """Unique hash for audit log integrity."""
    unique_str = f"{vessel_id}_{timestamp}"
    return hashlib.sha256(unique_str.encode()).hexdigest()[:12]

def sync_predictions_to_cloud():
    # 1. Google Cloud Connection
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        print("✅ Auth Success.")
    except Exception as e:
        print(f"❌ Auth Error: {e}")
        return

    # 2. Load ML Predictions
    if not os.path.exists(PREDICTIONS_CSV):
        print(f"❌ Error: {PREDICTIONS_CSV} not found.")
        return

    df_pred = pd.read_csv(PREDICTIONS_CSV)
    
    # Selecting the most relevant records (Top 1000 for a deep log)
    # This reflects a real operational shift
    existing_ids = set(sheet.col_values(1))
    prepared_rows = []

    # Sort by risk_score to prioritize visibility of critical alerts
    df_sorted = df_pred.sort_values(by='risk_score', ascending=False).head(1000)

    for _, row in df_sorted.iterrows():
        exec_time = row['execution_time']
        v_id = int(row['vessel_id'])
        p_id = generate_prediction_id(v_id, exec_time)
        
        if p_id not in existing_ids:
            prepared_rows.append([
                p_id,                          # A: prediction_id
                exec_time,                     # B: timestamp_prediction
                v_id,                          # C: vessel_id
                round(row['risk_score'], 4),    # D: risk_score
                row['risk_level'],             # E: risk_level
                row['recommended_action'],     # F: recommended_action
                "Pending Review"               # G: status
            ])

    # 3. Final Deployment in Chunks
    if prepared_rows:
        try:
            print(f"🚀 Syncing {len(prepared_rows)} records...")
            for i in range(0, len(prepared_rows), 100):
                sheet.append_rows(prepared_rows[i:i + 100])
            print("✅ Deployment complete.")
        except Exception as e:
            print(f"❌ Sync Failed: {e}")
    else:
        print("ℹ️ Everything up to date.")

if __name__ == "__main__":
    sync_predictions_to_cloud()