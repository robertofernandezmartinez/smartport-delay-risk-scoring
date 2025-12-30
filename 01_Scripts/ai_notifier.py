import pandas as pd
import requests
import datetime
import hashlib

# 1. Configuration with your EXACT Webhook URL
WEBHOOK_URL = "https://robertofernandezmartinez.app.n8n.cloud/webhook/vessel-alert"

def generate_prediction_id(vessel_id, timestamp):
    """Generates a unique ID for the Google Sheets row"""
    unique_str = f"{vessel_id}_{timestamp}"
    return hashlib.sha256(unique_str.encode()).hexdigest()[:12]

def send_to_n8n():
    """Processes predictions and triggers the n8n automation workflow"""
    try:
        # Load predictions from the output folder
        df = pd.read_csv('05_Outputs/predictions.csv')
    except FileNotFoundError:
        print("❌ Error: '05_Outputs/predictions.csv' not found.")
        return

    # Select the top 5 vessels with the highest risk scores
    top_vessels = df.sort_values(by='risk_score', ascending=False).head(5)

    print(f"🚀 Dispatching {len(top_vessels)} vessels to n8n...")

    for _, row in top_vessels.iterrows():
        # Using a new timestamp every time to force a new unique ID
        now_iso = datetime.datetime.utcnow().isoformat() + "Z"
        vessel_id = int(row['vessel_id'])
        
        payload = {
            "prediction_id": generate_prediction_id(vessel_id, now_iso),
            "timestamp_prediction": now_iso,
            "vessel_id": vessel_id,
            "risk_score": round(float(row['risk_score']), 2),
            "risk_level": row['risk_level'],
            "recommended_action": row['recommended_action'],
            "status": "Pending Review"
        }

        # Send to Webhook
        try:
            response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
            if response.status_code == 200:
                print(f"✅ Success: Vessel {vessel_id} sent.")
            else:
                print(f"⚠️ Warning: Status {response.status_code} for Vessel {vessel_id}")
        except Exception as e:
            print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    send_to_n8n()