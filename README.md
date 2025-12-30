# SmartPort AI: Early Warning Risk System 🚢🤖

An end-to-end Artificial Intelligence ecosystem designed for operational risk management in port terminals. It integrates **Machine Learning** for delay prediction, an **AI Agent (LLM)** for automated communication, and **Real-time Audit Logging**.

## 🚀 Project Overview
This project bridges the gap between static predictive models and real-world automation. The system filters thousands of vessel records, identifies those with a risk score higher than 80%, and triggers an AI Agent to generate professional instructions while maintaining a live audit trail of all actions.

## 🛠️ Tech Stack
- **Language:** Python 3.10 (Conda Environment)
- **Data Stack:** Pandas, Scikit-Learn, XGBoost
- **Orchestration:** n8n (Webhooks & Workflows)
- **Generative AI:** Google Gemini API
- **Storage & Auditing:** **Google Sheets (Logs Table)**
- **Infrastructure:** REST API (Webhooks)

## 📋 System Architecture
1. **Risk Filtering:** A Python script processes model predictions and detects critical vessels (Risk > 0.8).
2. **Triggering:** Data is sent via a POST request to a cloud-based n8n Webhook.
3. **AI Processing:** The AI Agent ingests the `vessel_id`, `risk_score`, and `recommended_action` to craft a professional response.
4. **Cloud Logging:** **The workflow automatically records the execution details, including the generated response, into a Google Sheets centralized dashboard.**
5. **Automated Output:** Generation of an executive notification tailored for port operations.

## 📊 Real-World Results & Auditing
The system provides a clear history of all high-risk interventions. Every notification is mirrored in the **Google Sheets Log**, allowing for performance reviews and operational transparency.

> **SAMPLE LOG ENTRY:**
> | Timestamp | Vessel ID | Risk Score | AI Instructions | Status |
> | :--- | :--- | :--- | :--- | :--- |
> | 2023-10-27 10:15 | V-102 | 0.94 | Reassign docking slot for Vessel V-102... | Success |

## ⚙️ Installation & Usage
1. Clone this repository.
2. Activate the environment: `conda activate smartport`.
3. Install dependencies: `pip install -r requirements.txt`.
4. **Google Sheets Setup:** Ensure your n8n Google Sheets node is connected to the project spreadsheet.
5. Import the `smartport_workflow.json` file into your n8n instance.
6. Run the notifier: `python 01_Scripts/ai_notifier.py`.