# SmartPort: Early Warning Risk System 🚢🤖

An end-to-end Artificial Intelligence ecosystem designed for operational risk management in port terminals. It integrates **Machine Learning** for delay prediction and an **AI Agent (LLM)** for automated critical alert communication.

## 🚀 Project Overview
This project bridges the gap between static predictive models and real-world automation. The system filters thousands of vessel records, identifies those with a risk score higher than 80%, and triggers an AI Agent to generate specific, professional instructions for the Harbor Master.

## 🛠️ Tech Stack
- **Language:** Python 3.10 (Conda Environment)
- **Data Stack:** Pandas, Scikit-Learn, XGBoost
- **Orchestration:** n8n (Webhooks & Workflows)
- **Generative AI:** Google Gemini API
- **Infrastructure:** REST API (Webhooks)

## 📋 System Architecture
1. **Risk Filtering:** A Python script processes model predictions and detects critical vessels (Risk > 0.8).
2. **Triggering:** Data is sent via a POST request to a cloud-based n8n Webhook.
3. **AI Processing:** The AI Agent ingests the `vessel_id`, `risk_score`, and `recommended_action`.
4. **Automated Output:** Generation of an executive notification tailored for port operations.

## 📊 Real-World Results
The system is capable of screening over **64,000 vessels** and generating automated responses such as:

> **SUBJECT: CRITICAL IMMEDIATE ACTION REQUIRED - Vessel ID 0 (Risk Score 0.99)** > *Harbor Master, Vessel ID 0 has been identified with a critical Risk Score of 0.99. IMMEDIATE ACTION IS REQUIRED: 1. Reassign docking slot for Vessel ID 0. 2. Notify all relevant tugboat crews.*

## ⚙️ Installation & Usage
1. Clone this repository.
2. Activate the environment: `conda activate smartport`.
3. Install dependencies: `pip install -r requirements.txt`.
4. Import the `smartport_workflow.json` file into your n8n instance.
5. Run the notifier: `python 01_Scripts/ai_notifier.py`.