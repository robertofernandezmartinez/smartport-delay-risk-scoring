import pandas as pd
import requests
import datetime
import hashlib

# 1. Configuración con tu URL exacta
WEBHOOK_URL = "https://robertofernandezmartinez.app.n8n.cloud/webhook-test/vessel-alert"

def generate_prediction_id(vessel_id, timestamp):
    unique_str = f"{vessel_id}_{timestamp}"
    return hashlib.sha256(unique_str.encode()).hexdigest()[:12]

def send_to_n8n():
    try:
        # Cargamos los datos
        df = pd.read_csv('05_Outputs/predictions.csv')
    except FileNotFoundError:
        print("❌ Error: No se encuentra el archivo '05_Outputs/predictions.csv'")
        return

    # Cogemos los 5 barcos con más riesgo
    top_vessels = df.sort_values(by='risk_score', ascending=False).head(5)

    print(f"🚀 Enviando datos a n8n...")

    for _, row in top_vessels.iterrows():
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

        # Enviar al Webhook
        try:
            response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
            if response.status_code == 200:
                print(f"✅ Barco {vessel_id} enviado con éxito")
            else:
                print(f"⚠️ Error {response.status_code} en barco {vessel_id}")
        except Exception as e:
            print(f"❌ Error de conexión: {e}")

if __name__ == "__main__":
    send_to_n8n()