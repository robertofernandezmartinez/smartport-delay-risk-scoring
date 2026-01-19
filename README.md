# 🚢 SmartPort AI: Predictive Logistics & Supply Chain Intelligence
**Real-Time Maritime Risk Monitoring & Inventory Impact Analysis**

SmartPort AI is a comprehensive **maritime intelligence ecosystem** designed to predict vessel delays and analyze their direct impact on global supply chains. 

By merging **Machine Learning (XGBoost)**, **Real-Time Data Orchestration**, and **Generative AI (GPT-4o)**, this system transforms raw AIS movement data into actionable business decisions.

![](images/smartport-image.png)

---

## 🎯 Business Logic & Problem Statement

In maritime logistics, a delay of more than **120 minutes** (the critical berthing window) creates a ripple effect of economic loss. SmartPort AI solves this by answering:

1.  **Prediction:** Which vessels will exceed the 120-minute delay threshold?
2.  **Impact:** How does this delay affect our current **warehouse stock levels**?
3.  **Action:** What priority measures should operations teams take right now?

---

## 🏗️ System Architecture: The Three-Layer Ecosystem

![SmartPort AI Architecture](images/architecture_diagram.png)

SmartPort AI is built as a modular pipeline designed for scalability:

### 1. The ML Engine (Predictive Layer)
* **Model:** XGBoost Classifier trained on AIS movement patterns.
* **Feature Engineering:** Analyzes speed stability, heading variance, and historical congestion.
* **Output:** Generates a `risk_score` (0-1) and categorizes vessels into **CRITICAL**, **WARNING**, or **NORMAL**.

### 2. The Cloud Audit Layer (Source of Truth)
* **Platform:** Google Sheets API.
* **Function:** Acts as a lightweight, auditable data warehouse and dashboard.
* **Traceability:** Every prediction is hashed using **SHA-256** (`prediction_id`) to ensure data integrity and prevent duplicates.

### 3. The Command & Control Center (Interaction Layer)
* **Technology:** Python-Telegram-Bot + OpenAI API.
* **Watchman:** Proactively scans the dashboard every 60 seconds for new critical risks.
* **Analyst:** A natural-language interface allowing operators to query the state of the port and receive strategic advice.

---

## 🔗 The "Bridge": Supply Chain Integration
**Where Logistics meets Inventory.**

This project features a unique integration with an independent **Stock-Out Prediction Engine**. By cross-referencing maritime delays with warehouse demand, the system calculates **Compound Risk**.

* **Logic:** `(Estimated Arrival Time) > (Predicted Stock-Out Date) = Critical Supply Chain Breach`.
* **Value:** Instead of just reporting a late ship, the system identifies **which specific products** will go out of stock due to that delay.



---

## 🚦 Risk & Priority Matrix

| Risk Level | Threshold | Operational Meaning | Supply Chain Impact |
| :--- | :--- | :--- | :--- |
| **CRITICAL** | > 0.80 | High likelihood of >120m delay | Immediate Stock-Out risk for assigned cargo. |
| **WARNING** | 0.50 - 0.80 | Elevated risk; AIS monitoring req. | Potential safety stock depletion. |
| **NORMAL** | < 0.50 | On-schedule operations | Routine inventory replenishment. |

---

## 🛠️ Tech Stack

* **Languages:** Python 3.10+
* **AI/ML:** XGBoost, Scikit-learn, OpenAI GPT-4o-mini.
* **Data/Cloud:** Google Sheets API (gspread), Pandas.
* **Deployment:** Telegram Bot API, Railway / Local Environment.
* **Security:** SHA-256 Hashing, Environment Variables (`.env`).

---

## 📊 Dashboard Structure

The Google Sheets dashboard is structured for fast scanning and operational audits:

| Column | Description |
| :--- | :--- |
| `prediction_id` | Unique SHA-256 hash for audit and traceability. |
| `timestamp` | Exact time the model executed the inference. |
| `vessel_id` | Unique identifier for the vessel. |
| `risk_score` | Probability of delay >120 minutes. |
| `risk_level` | Operational category (CRITICAL / WARNING / NORMAL). |
| `action` | AI-generated operational recommendation. |

---

## 🚀 Future Roadmap
- [ ] **Dynamic Re-routing:** Suggesting alternative ports based on congestion.
- [ ] **Financial Impact:** Estimating the USD cost of each hour of delay.
- [ ] **Computer Vision:** Integrating satellite imagery to verify AIS positions.