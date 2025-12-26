import pandas as pd
import requests
import datetime
import hashlib
import json

# 1. Configuración
WEBHOOK_URL = "TU_URL_DE_N8N_AQUI" # Reemplaza con tu URL de n8n

def generate_prediction_id(vessel_id, timestamp):
    """Genera un ID único para evitar duplicados en Google Sheets (Upsert)"""
    unique_str = f"{vessel_id}_{timestamp}"
    return hashlib.sha256(unique_str.encode()).hexdigest()[:12]

def send_to_n8n():
    # Cargar las predicciones
    df = pd.read_csv('05_Outputs/predictions.csv')
    
    # En esta Fase 2, enviamos los datos más relevantes 
    # (n8n decidirá si alerta o solo guarda el log)
    top_vessels = df.sort_values(by='delay_risk_score', ascending=False).head(5)

    for _, row in top_vessels.iterrows():
        # Preparar datos limpios y estandarizados
        now_iso = datetime.datetime.utcnow().isoformat() + "Z"
        vessel_id = int(row['vessel_id'])
        risk_score = round(float(row['delay_risk_score']), 2)
        
        # Determinar nivel de riesgo para la lógica de n8n
        risk_level = "Critical" if risk_score > 0.8 else "Elevated"
        
        payload = {
            "prediction_id": generate_prediction_id(vessel_id, now_iso),
            "timestamp_prediction": now_iso,
            "vessel_id": vessel_id,
            "delay_minutes": int(row['predicted_delay_minutes']),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "status": "Pending Review",
            "recommended_action": "Reassign docking slot" if risk_score > 0.8 else "Monitor status"
        }

        # Enviar al Webhook
        try:
            response = requests.post(WEBHOOK_URL, json=payload)
            if response.status_code == 200:
                print(f"✅ Data for Vessel {vessel_id} sent successfully (ID: {payload['prediction_id']})")
            else:
                print(f"⚠️ Error sending Vessel {vessel_id}: {response.status_code}")
        except Exception as e:
            print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    send_to_n8n()