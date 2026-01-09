import pandas as pd
import datetime
import hashlib
import gspread
import os
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURATION (SmartPort AI Business Logic) ---
CSV_SOURCE = '05_Outputs/predictions.csv'
CREDENTIALS_FILE = "credentials.json"
SPREADSHEET_ID = "1aTJLlg4YNT77v1PLQccKl8ZCADBJN0U8kncTBvf43P0"

def generate_prediction_id(vessel_id, timestamp):
    """Generates a unique audit hash for the row."""
    unique_str = f"{vessel_id}_{timestamp}"
    return hashlib.sha256(unique_str.encode()).hexdigest()[:12]

def sync_predictions_to_sheets():
    """
    Syncs ML predictions and applies the Business Decision Layer:
    - 120min Threshold logic
    - Economic Impact classification
    - Risk Level mapping
    """
    # 1. Google Sheets Auth
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        print("✅ Auth Success: SmartPort Cloud connected.")
    except Exception as e:
        print(f"❌ Auth Error: {e}")
        return

    # 2. Load ML Output
    if not os.path.exists(CSV_SOURCE):
        print(f"❌ Error: {CSV_SOURCE} not found.")
        return

    df = pd.read_csv(CSV_SOURCE)
    existing_ids = sheet.col_values(1)
    
    # Sorting by risk to prioritize critical cases
    top_vessels = df.sort_values(by='risk_score', ascending=False).head(100)

    prepared_rows = []
    for _, row in top_vessels.iterrows():
        v_id = int(row['vessel_id'])
        exec_time = row['execution_time']
        r_score = float(row['risk_score'])
        
        # BUSINESS LOGIC LAYER
        # We assume delay_minutes is derived from the model's score for the demo
        # (e.g., Score 1.0 = 240 min, Score 0.5 = 120 min)
        delay_min = int(r_score * 240) 
        
        # Severity and Economic Impact logic
        if delay_min > 300:
            impact = "HIGH (Dock Blockage)"
        elif delay_min >= 120:
            impact = "MODERATE"
        else:
            impact = "LOW (Operational Margin)"

        p_id = generate_prediction_id(v_id, exec_time)
        
        if p_id not in existing_ids:
            # MAPPING: Matches the new professional structure
            prepared_rows.append([
                p_id,                       # A: prediction_id
                exec_time,                  # B: timestamp_prediction
                v_id,                       # C: vessel_id
                round(r_score, 3),          # D: risk_score
                row['risk_level'],          # E: risk_level (CRITICAL/WARNING/NORMAL)
                delay_min,                  # F: predicted_delay_minutes
                impact,                     # G: economic_impact
                row['recommended_action'],  # H: recommended_action
                "Pending Review"            # I: status
            ])

    # 3. Final Deployment
    if prepared_rows:
        try:
            sheet.append_rows(prepared_rows)
            print(f"🚀 Success: {len(prepared_rows)} records synced with Impact Analysis.")
        except Exception as e:
            print(f"❌ Upload Failed: {e}")
    else:
        print("ℹ️ Status: Cloud Dashboard is already up to date.")

if __name__ == "__main__":
    sync_predictions_to_sheets()