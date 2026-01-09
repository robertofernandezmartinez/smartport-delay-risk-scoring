import pandas as pd
import gspread
import hashlib
from oauth2client.service_account import ServiceAccountCredentials

CSV_SOURCE = '05_Outputs/predictions.csv'
CREDENTIALS_FILE = "credentials.json"
SPREADSHEET_ID = "1aTJLlg4YNT77v1PLQccKl8ZCADBJN0U8kncTBvf43P0"

def sync_balanced_dashboard():
    # 1. Connection
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds).open_by_key(SPREADSHEET_ID).sheet1

    # 2. Data Load
    df = pd.read_csv(CSV_SOURCE)
    
    # 3. Strategic Sampling: Ensure all risk levels are visible
    df_sync = pd.concat([
        df[df['risk_level'] == 'NORMAL'], 
        df[df['risk_level'] == 'CRITICAL'].head(500),
        df[df['risk_level'] == 'WARNING'].head(500)
    ])

    # 4. Preparation
    rows = []
    for _, r in df_sync.iterrows():
        # Unique ID to prevent duplication
        p_id = hashlib.sha256(f"{r['vessel_id']}_{r['execution_time']}".encode()).hexdigest()[:12]
        rows.append([
            p_id, 
            r['execution_time'], 
            int(r['vessel_id']), 
            round(r['risk_score'], 3), 
            r['risk_level'], 
            r['recommended_action'], 
            "Pending"
        ])

    # 5. Clean and Update Sheet
    client.clear()
    headers = ["prediction_id", "timestamp", "vessel_id", "risk_score", "risk_level", "action", "status"]
    client.insert_row(headers, 1)
    client.append_rows(rows)
    
    print(f"✅ Sync Complete: {len(rows)} balanced records uploaded to Dashboard.")

if __name__ == "__main__":
    sync_balanced_dashboard()