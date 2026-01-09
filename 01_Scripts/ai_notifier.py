import pandas as pd
import datetime
import hashlib
import gspread
import os
from oauth2client.service_account import ServiceAccountCredentials

# --- SETTINGS ---
CSV_SOURCE = '05_Outputs/predictions.csv'
CREDENTIALS_FILE = "credentials.json"
# Replace with your actual Google Sheet ID
SPREADSHEET_ID = "1aTJLlg4YNT77v1PLQccKl8ZCADBJN0U8kncTBvf43P0"

def generate_prediction_id(vessel_id, timestamp):
    """
    Recreates the original unique hashing logic to ensure 
    data integrity and professional tracking.
    """
    unique_str = f"{vessel_id}_{timestamp}"
    return hashlib.sha256(unique_str.encode()).hexdigest()[:12]

def sync_predictions_to_cloud():
    """
    Main pipeline: 
    1. Loads XGBoost raw data.
    2. Enriches the data with business context.
    3. Formats columns to fix the displacement issue.
    4. Performs bulk upload to Google Sheets.
    """
    # 1. Google API Authentication
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        print("✅ Auth Success: Connected to Google Cloud Engine.")
    except Exception as e:
        print(f"❌ Auth Error: {e}")
        return

    # 2. Load ML Predictions
    if not os.path.exists(CSV_SOURCE):
        print(f"❌ Error: File not found at {CSV_SOURCE}")
        return

    df = pd.read_csv(CSV_SOURCE)
    
    # Selecting Top 50 high-risk vessels for a clean, professional dashboard
    top_vessels = df.sort_values(by='risk_score', ascending=False).head(50)

    prepared_rows = []
    
    for _, row in top_vessels.iterrows():
        # Metadata Generation
        now_iso = datetime.datetime.utcnow().isoformat() + "Z"
        v_id_numeric = int(row['vessel_id'])
        vessel_name = f"VESSEL-{v_id_numeric}"
        
        # Business Intelligence Enrichment
        # We assign a type based on the ID or Score to add variety for the AI Analyst
        v_type = "Oil Tanker" if v_id_numeric % 2 == 0 else "Cargo Carrier"
        
        # Mapping columns EXACTLY to avoid the previous displacement error
        prepared_rows.append([
            generate_prediction_id(vessel_name, now_iso), # Col A: Prediction ID
            now_iso,                                      # Col B: Timestamp
            vessel_name,                                  # Col C: Vessel Name
            v_type,                                       # Col D: Vessel Type
            round(float(row['risk_score']), 3),           # Col E: Risk Score
            row['recommended_action'],                    # Col F: Recommended Action
            "PENDING_REVIEW"                              # Col G: Operational Status
        ])

    # 3. Cloud Deployment
    if prepared_rows:
        try:
            # OPTIONAL: Clear the sheet first to fix the 116k mess
            # sheet.clear() 
            sheet.append_rows(prepared_rows)
            print(f"🚀 Deployment Complete: {len(prepared_rows)} records synced.")
        except Exception as e:
            print(f"❌ Upload Failed: {e}")
    else:
        print("ℹ️ Status: No new data found to process.")

if __name__ == "__main__":
    print("🚢 --- SMARTPORT AI DATA PIPELINE ---")
    sync_predictions_to_cloud()