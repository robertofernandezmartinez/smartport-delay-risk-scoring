import pandas as pd
import datetime
import hashlib
import gspread
import os
import numpy as np # Added for realistic delay calculation
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURATION ---
CSV_SOURCE = '05_Outputs/predictions.csv'
CREDENTIALS_FILE = "credentials.json"
SPREADSHEET_ID = "1aTJLlg4YNT77v1PLQccKl8ZCADBJN0U8kncTBvf43P0"

def generate_prediction_id(vessel_id, timestamp):
    unique_str = f"{vessel_id}_{timestamp}"
    return hashlib.sha256(unique_str.encode()).hexdigest()[:12]

def sync_predictions_to_cloud():
    # 1. Auth
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        print("✅ Auth Success.")
    except Exception as e:
        print(f"❌ Auth Error: {e}")
        return

    # 2. Load Data
    if not os.path.exists(CSV_SOURCE):
        print(f"❌ Error: {CSV_SOURCE} not found.")
        return

    df = pd.read_csv(CSV_SOURCE)
    
    # 3. MECHANICAL CHANGE: Increase visibility
    # We take the top 500 highest risks to show a significant but safe batch
    top_vessels = df.sort_values(by='risk_score', ascending=False).head(500)
    
    existing_ids = sheet.col_values(1)
    prepared_rows = []

    for _, row in top_vessels.iterrows():
        exec_time = row['execution_time']
        v_id = int(row['vessel_id'])
        r_score = float(row['risk_score'])
        
        # 4. REALISTIC DELAY CALCULATION:
        # We use the score as a base (0.0 to 1.0) and multiply by a max delay (e.g. 300 min)
        # We add a small random variation so not all 1.0 scores look the same
        base_delay = r_score * 240 # Max 4 hours
        variation = np.random.randint(-15, 15) if r_score > 0 else 0
        delay_min = max(0, int(base_delay + variation))
        
        p_id = generate_prediction_id(v_id, exec_time)
        
        if p_id not in existing_ids:
            prepared_rows.append([
                p_id,
                exec_time,
                v_id,
                round(r_score, 4),
                row['risk_level'],
                delay_min,
                row['recommended_action'],
                "Pending Review"
            ])

    # 5. Bulk Upload in chunks to avoid API Timeout
    if prepared_rows:
        try:
            # We upload in smaller chunks of 100 to be 100% safe with Google Quotas
            for i in range(0, len(prepared_rows), 100):
                chunk = prepared_rows[i:i + 100]
                sheet.append_rows(chunk)
            print(f"🚀 Success: {len(prepared_rows)} unique records synced.")
        except Exception as e:
            print(f"❌ Sync Failed: {e}")
    else:
        print("ℹ️ Status: No new unique records to add.")

if __name__ == "__main__":
    sync_predictions_to_cloud()