import os
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURATION ---
CSV_SOURCE = "05_Outputs/predictions.csv"
CREDENTIALS_FILE = "credentials.json"
SPREADSHEET_ID = "1aTJLlg4YNT77v1PLQccKl8ZCADBJN0U8kncTBvf43P0" # Asegúrate de que este ID sea correcto

def sync_ml_predictions():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return

    if not os.path.exists(CSV_SOURCE):
        print(f"❌ Error: {CSV_SOURCE} not found.")
        return

    # Cargamos el CSV y limpiamos los nombres de las columnas automáticamente
    df = pd.read_csv(CSV_SOURCE)
    df.columns = df.columns.str.strip().str.lower() # Elimina espacios y pasa a minúsculas
    
    print(f"DEBUG: Processed columns: {df.columns.tolist()}")

    # Obtenemos IDs existentes para no duplicar
    existing_ids = [str(i) for i in sheet.col_values(1)]
    
    new_data_batch = []
    
    # Mapeo flexible para evitar el KeyError
    for _, row in df.iterrows():
        # Intentamos obtener el ID usando varios nombres posibles
        p_id = str(row.get('prediction_id') or row.get('id') or row.iloc[0])
        
        if p_id not in existing_ids:
            new_data_batch.append([
                p_id,
                row.get('timestamp_prediction', ''),
                row.get('vessel_id', ''),
                row.get('risk_score', ''),
                row.get('risk_level', ''),
                row.get('recommended_action', ''),
                "NEW"
            ])

    if new_data_batch:
        sheet.append_rows(new_data_batch)
        print(f"🚀 Success: {len(new_data_batch)} rows synced.")
    else:
        print("ℹ️ No new data to upload.")

if __name__ == "__main__":
    sync_ml_predictions()