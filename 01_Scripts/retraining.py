import os
import pandas as pd
import cloudpickle
from sklearn.metrics import recall_score

# Paths
BASE_PATH = '/Users/rober/smartport-delay-risk-scoring/'
TRAIN_DATA = os.path.join(BASE_PATH, '02_Data/03_Working/work_fs.csv')
SKELETON = os.path.join(BASE_PATH, '04_Models/pipe_retraining.pkl')
EXECUTION_PIPE = os.path.join(BASE_PATH, '04_Models/pipe_execution.pkl')

def run_retraining():
    # Load and Clean
    df = pd.read_csv(TRAIN_DATA)
    
    # Validation: Drop rows where target is missing (ML cannot learn from NaN targets)
    df = df.dropna(subset=['delay_flag'])
    
    X = df.drop(columns=['delay_flag'])
    y = df['delay_flag']
    
    # Load Skeleton
    with open(SKELETON, 'rb') as f:
        pipe = cloudpickle.load(f)
    
    # Train
    pipe.fit(X, y)
    
    # Audit (Threshold 0.02)
    probs = pipe.predict_proba(X)[:, 1]
    recall = recall_score(y, (probs >= 0.02).astype(int))
    
    if recall >= 0.95:
        with open(EXECUTION_PIPE, 'wb') as f:
            cloudpickle.dump(pipe, f)
        print(f"✔ retraining.py: Model promoted with Recall: {recall:.4f}")
    else:
        print(f"✘ retraining.py: Recall {recall:.4f} below 0.95 limit.")

if __name__ == "__main__":
    run_retraining()