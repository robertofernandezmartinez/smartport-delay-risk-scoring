# 🚢 SmartPort AI: Real-Time Maritime Risk Monitoring

SmartPort AI is a professional-grade autonomous system designed to monitor vessel risks and manage port operations via AI. It integrates Google Sheets as a live database, OpenAI for decision-making, and Telegram for real-time alerting and interaction.



## 🚀 Core Features

* **Dual-Engine Architecture**: 
    * **The Watchman (Background Monitoring)**: Automatically scans maritime logs every 60 seconds. If a vessel exceeds a 0.8 risk threshold, it triggers an immediate Telegram alert.
    * **The Analyst (AI Assistant)**: A conversational interface powered by GPT-4o-mini that answers complex queries about port status, delays, and vessel prioritization.
* **Anti-Spam Logic**: Integrated memory management to ensure critical alerts are only sent once per risk event.
* **Robust Data Handling**: Intelligent processing of inconsistent datasets, including empty fields and data grouping by Vessel ID.
* **Cloud Native**: Fully deployed on Railway for 24/7 autonomous operation.

## 🛠️ Tech Stack

* **Language**: Python 3.x (Asynchronous)
* **AI Engine**: OpenAI API (GPT-4o-mini)
* **Database**: Google Sheets API (Real-time CRUD)
* **Communication**: Telegram Bot API
* **Infrastructure**: Railway (PaaS)
* **Security**: Environment Variable Encryption (.env)

## 📊 System Architecture

The system follows a reactive pattern:
1.  **Data Ingestion**: Fetches live vessel logs from Google Sheets.
2.  **Processing**: 
    * The `JobQueue` monitors risk thresholds asynchronously.
    * The `ChatHandler` processes natural language queries using RAG-lite (Resource Augmented Generation).
3.  **Delivery**: Sends structured Markdown alerts and professional reports via Telegram.

## ⚙️ Setup & Deployment

1.  **Environment Variables**:
    Create a `.env` file with the following:
    ```env
    TELEGRAM_TOKEN=your_bot_token
    OPENAI_API_KEY=your_openai_key
    SPREADSHEET_ID=your_google_sheet_id
    TELEGRAM_CHAT_ID=your_personal_chat_id
    ```
2.  **Installation**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Execution**:
    ```bash
    python main.py
    ```

## 📈 Future Roadmap
* Implementation of persistent SQLite history for conversation context.
* Automated PDF report generation for port authorities.
* Integration with live AIS (Automatic Identification System) data APIs.

---
Developed by Roberto Fernández - 2025. Specialized in AI Operations and Maritime Logistics.