import os
import pandas as pd
import cloudpickle
from datetime import datetime

# Paths
BASE_PATH = '/Users/rober/smartport-delay-risk-scoring/'
MODEL_FILE = os.path.join(BASE_PATH, '04_Models/pipe_execution.pkl')
SOURCE_DATA = os.path.join(BASE_PATH, '02_Data/03_Working/work_fs.csv')
OUTPUT_CSV = os.path.join(BASE_PATH, '05_Outputs/predictions.csv')

# Define Actionable Business Logic
# This allows us to change the strategy without changing the code
DECISION_MAP = {
    'CRITICAL': 'IMMEDIATE: Reassign Docking Slot & Notify Tugboats',
    'WARNING': 'PROACTIVE: Request GPS/ETA update from Vessel',
    'NORMAL': 'ROUTINE: Maintain standard schedule'
}

def run_execution():
    if not os.path.exists(MODEL_FILE):
        print("✘ Error: pipe_execution.pkl not found.")
        return

    with open(MODEL_FILE, 'rb') as f:
        model = cloudpickle.load(f)
    
    df = pd.read_csv(SOURCE_DATA)
    
    # 1. Prepare Features
    X_live = df.drop(columns=['delay_flag']) if 'delay_flag' in df.columns else df
    
    # 2. Get Risk Scores
    probs = model.predict_proba(X_live)[:, 1]
    
    # 3. Create Results with Decision Layer
    results = pd.DataFrame()
    results['vessel_id'] = df.index # In production, replace with IMO/Ship Name
    results['risk_score'] = probs
    
    # Map probabilities to Categories
    results['risk_level'] = results['risk_score'].apply(
    lambda x: 'CRITICAL' if x >= 0.99 else (  # Only the absolute worst cases
               'WARNING' if x >= 0.02 else   # The safety net remains
               'NORMAL')    )
    
    # Map Categories to PHYSICAL ACTIONS
    results['recommended_action'] = results['risk_level'].map(DECISION_MAP)
    
    results['execution_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 4. Save
    results.to_csv(OUTPUT_CSV, index=False)
    print(f"✔ execution.py: Decisions saved in {OUTPUT_CSV}")

if __name__ == "__main__":
    run_execution()

df = pd.read_csv('/Users/rober/smartport-delay-risk-scoring/05_Outputs/predictions.csv')
print(df['risk_level'].value_counts())
print("\nAverage Risk Score:", df['risk_score'].mean())