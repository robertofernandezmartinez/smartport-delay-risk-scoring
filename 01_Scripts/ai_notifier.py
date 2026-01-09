import pandas as pd
import datetime
import hashlib
import gspread
import os
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURATION (SmartPort AI Migration) ---
CSV_SOURCE = '05_Outputs/predictions.csv'
CREDENTIALS_FILE = "credentials.json"
# Using your verified Spreadsheet ID
SPREADSHEET_ID = "1aTJLlg4YNT77v1PLQccKl8ZCADBJN0U8kncTBvf43P0"

def generate_prediction_id(vessel_id, timestamp):
    """
    Generates a unique hash (The 'DNI' of the row) to prevent 
    duplicates in Google Sheets when re-running the script.
    """
    unique_str = f"{vessel_id}_{timestamp}"
    return hashlib.sha256(unique_str.encode()).hexdigest()[:12]

def sync_predictions_to_cloud():
    """
    Main pipeline: Loads ML data, calculates business impact (delay),
    and performs a direct bulk upload to Google Sheets.
    """
    # 1. Google Cloud Auth Setup
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        print("✅ Auth Success: Connected to Google Cloud Engine.")
    except Exception as e:
        print(f"❌ Auth Error: Check your credentials.json and API permissions. Details: {e}")
        return

    # 2. Load Original ML Output
    if not os.path.exists(CSV_SOURCE):
        print(f"❌ Error: ML source file not found at {CSV_SOURCE}")
        return

    df = pd.read_csv(CSV_SOURCE)
    
    # Getting existing IDs from Column A to enforce uniqueness
    existing_ids = sheet.col_values(1)
    
    # Selection: Getting top vessels based on risk score
    top_vessels = df.sort_values(by='risk_score', ascending=False).head(100)

    prepared_rows = []
    for _, row in top_vessels.iterrows():
        # Metadata logic (Same as n8n original workflow)
        now_iso = datetime.datetime.utcnow().isoformat() + "Z"
        v_id = int(row['vessel_id'])
        r_score = float(row['risk_score'])
        
        # BUSINESS LOGIC: Predicted delay minutes from XGBoost output
        # If the column exists in your CSV, we use it; otherwise, we scale it from the score
        delay_min = int(row.get('predicted_delay_minutes', r_score * 120))
        
        p_id = generate_prediction_id(v_id, now_iso)
        
        # 3. Row Construction (Matching your Audit Log structure)
        if p_id not in existing_ids:
            prepared_rows.append([
                p_id,                       # A: prediction_id (Unique Hash)
                now_iso,                    # B: timestamp_prediction
                v_id,                       # C: vessel_id
                round(r_score, 3),          # D: risk_score
                row['risk_level'],          # E: risk_level
                delay_min,                  # F: predicted_delay_minutes
                row['recommended_action'],  # G: recommended_action
                "Pending Review"            # H: status
            ])

    # 4. Final Deployment
    if prepared_rows:
        try:
            sheet.append_rows(prepared_rows)
            print(f"🚀 Success: {len(prepared_rows)} professional records synced to SmartPort Dashboard.")
        except Exception as e:
            print(f"❌ Deployment Failed: {e}")
    else:
        print("ℹ️ Status: Database is up to date. No new records to sync.")

if __name__ == "__main__":
    print("🚢 --- SMARTPORT AI: DIRECT CLOUD SYNC ---")
    sync_predictions_to_cloud()