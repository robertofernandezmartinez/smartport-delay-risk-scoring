import pandas as pd
import gspread
import hashlib
import os
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURATION ---
PROJECT_PATH = '/Users/rober/smartport-ai-risk-early-warning'
CSV_SOURCE = os.path.join(PROJECT_PATH, '05_Outputs/risk_alerts.csv')
CREDENTIALS_FILE = os.path.join(PROJECT_PATH, "credentials.json")
SPREADSHEET_ID = "1aTJLlg4YNT77v1PLQccKl8ZCADBJN0U8kncTBvf43P0"

def sync_balanced_dashboard():
    """
    Reads the latest risk alerts and synchronizes them with the Google Sheets Dashboard.
    """
    # 1. Connection setup
    print("Connecting to Google Sheets...")
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
        client = gspread.authorize(creds).open_by_key(SPREADSHEET_ID).sheet1
    except Exception as e:
        print(f"✘ Connection Error: {e}")
        return

    # 2. Data Load
    if not os.path.exists(CSV_SOURCE):
        print(f"✘ Error: {CSV_SOURCE} not found. Please run the execution script first.")
        return
        
    df = pd.read_csv(CSV_SOURCE)
    
    # 3. Strategic Sampling: Balancing the dashboard view
    # We prioritize alerts (Critical/Warning) but show some Normal cases for context
    df_sync = pd.concat([
        df[df['risk_level'] == 'NORMAL'].head(100), 
        df[df['risk_level'] == 'CRITICAL'].head(500),
        df[df['risk_level'] == 'WARNING'].head(500)
    ]).fillna("N/A")

    # 4. Data Preparation (Mapping internal names to Dashboard columns)
    rows = []
    for _, r in df_sync.iterrows():
        # Generate a unique 12-char ID based on vessel and time
        raw_id = f"{r['vessel_index']}_{r['timestamp']}"
        p_id = hashlib.sha256(raw_id.encode()).hexdigest()[:12]
        
        rows.append([
            p_id,                         # prediction_id
            str(r['timestamp']),          # timestamp_prediction
            int(r['vessel_index']),       # vessel_id
            float(round(r['risk_score'], 3)), # risk_score
            str(r['risk_level']),         # risk_level
            str(r['recommended_action']), # recommended_action
            "Pending Review"              # status
        ])

    # 5. Clean and Update Sheet
    print(f"Uploading {len(rows)} records to Dashboard...")
    client.clear()
    
    # Define Headers exactly as requested
    headers = [
        "prediction_id", 
        "timestamp_prediction", 
        "vessel_id", 
        "risk_score", 
        "risk_level", 
        "recommended_action", 
        "status"
    ]
    
    # Upload headers and data
    client.insert_row(headers, 1)
    if rows:
        client.append_rows(rows)
        print("✅ Sync Complete: SmartPort AI Operational Logs updated.")
    else:
        print("⚠ Warning: No data available for sync.")

if __name__ == "__main__":
    sync_balanced_dashboard()