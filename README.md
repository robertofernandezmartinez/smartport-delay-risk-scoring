# 🚢 SmartPort AI: Real-Time Maritime Delay Prediction & Management

SmartPort AI is an end-to-end data engineering and machine learning solution designed to predict and manage vessel delays in busy port environments. By combining a **Gradient Boosting (XGBoost)** model with a cloud-based audit system and a real-time notification layer, the project transforms raw AIS data into actionable maritime intelligence.



## 🎯 Project Focus & Business Logic
The core objective is to identify vessels that will exceed the **120-minute (2-hour) delay threshold**, which is the critical "berthing window" in port logistics.

* **Target:** Predict delays > 120 minutes.
* **Actionability:** Automated risk categorization to assist port operators in real-time decision-making.
* **Architecture:** A seamless pipeline from local ML execution to Google Cloud storage and Telegram instant alerting.

## 🏗️ Technical Architecture
The system is built as a unified ecosystem where data flows through three distinct layers:

1.  **ML Engine:** XGBoost model trained on engineered AIS features (speed delta, movement stability, heading changes).
2.  **Cloud Data Warehouse:** Google Sheets API serves as a real-time audit log and operational dashboard.
3.  **Command & Control:** A unified Telegram Bot for both push notifications (Critical alerts) and pull queries (Vessel status).



---

## 🚀 Key Components

### 1. Machine Learning Execution (`execution.py`)
The pipeline processes the `work_fs.csv` dataset, extracting features and running them through the trained model.
* **Probability Scoring:** Outputs a `risk_score` (0 to 1).
* **Decision Map:**
    * **CRITICAL (> 0.8):** Immediate intervention (e.g., Reassign docking slot).
    * **WARNING (0.5 - 0.8):** Proactive monitoring of GPS/ETA updates.
    * **NORMAL (< 0.5):** Routine operations.

### 2. Strategic Cloud Dashboard (Google Sheets)
To ensure high-speed decision-making, the system syncs a **balanced operational sample** rather than raw Big Data:
* **Total Visibility:** Includes all 'NORMAL' cases to maintain a baseline.
* **Strategic Focus:** Synchronizes top 'CRITICAL' and 'WARNING' cases.
* **Audit Integrity:** Every entry uses a unique `prediction_id` (SHA-256 hash) to prevent duplicates and ensure data lineage.

### 3. Unified Telegram Interface
The bot acts as the central hub for the port operator, maintaining all interactions in a single window:
* **Push Alerts:** Immediate notifications for **CRITICAL** vessels.
* **Interactive Queries:** Allows the operator to ask about specific vessels or overall port status.
* **Closed-Loop System:** Bridges the gap between a prediction and a physical action in the port.

---

## 📊 Dashboard Structure
The Google Sheets dashboard is organized for high-speed decision-making:

| Column | Description |
| :--- | :--- |
| `prediction_id` | Unique alphanumeric hash for audit tracking. |
| `timestamp` | Exact execution time of the ML prediction. |
| `vessel_id` | Original vessel identifier from the ML process. |
| `risk_score` | Confidence level of the XGBoost model. |
| `risk_level` | Executive category (CRITICAL, WARNING, NORMAL). |
| `action` | Recommended business action based on the Decision Map. |
| `status` | Operational state (e.g., Pending, Resolved). |

---

## 🛠️ Setup & Usage
1.  **ML Inference:** Run `python 01_Scripts/execution.py` to generate new predictions.
2.  **Cloud Sync:** Run `python 01_Scripts/ai_notifier.py` to update the Google Sheets dashboard.
3.  **Monitoring:** Activate the Telegram Bot to receive real-time notifications and perform queries.

## 📈 Future Roadmap
* **Economic Impact Scaling:** Integrating cargo value to calculate the financial loss per minute of delay.
* **Live AIS Integration:** Connecting the pipeline to a real-time AIS stream for true 24/7 monitoring.

---
Developed by Roberto Fernández - 2025. Specialized in AI Operations and Maritime Logistics.