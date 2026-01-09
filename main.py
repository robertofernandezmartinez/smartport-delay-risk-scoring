import os
import gspread
import asyncio
from openai import OpenAI
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from oauth2client.service_account import ServiceAccountCredentials

# 1. Configuration and Environment Setup
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Global set to track notified vessels and prevent notification loops (spam)
sent_alerts = set()

def get_data():
    """Authenticates with Google Sheets and retrieves all records."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    gc = gspread.authorize(creds)
    # Uses the ID from environment variables for security and portability
    return gc.open_by_key(os.getenv("SPREADSHEET_ID")).sheet1.get_all_records()

# 2. Automated Risk Monitoring Logic (Replaces n8n)
async def check_vessel_risk(context: ContextTypes.DEFAULT_TYPE):
    global sent_alerts
    try:
        data = get_data()
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not chat_id:
            print("Monitoring Error: TELEGRAM_CHAT_ID is missing in environment variables.")
            return

        current_high_risks = set()

        for vessel in data:
            v_id = str(vessel.get('vessel_id', 'Unknown'))
            raw_risk = vessel.get('risk_score', '')

            # Robustness: Skip empty cells or rows without risk data
            if not str(raw_risk).strip():
                continue

            try:
                risk = float(raw_risk)
            except ValueError:
                # Logs error but keeps the bot running
                print(f"Skipping row for {v_id}: Cannot convert '{raw_risk}' to number.")
                continue

            # Alert logic: Trigger if risk > 0.8 and not already notified
            if risk > 0.8:
                current_high_risks.add(v_id)
                if v_id not in sent_alerts:
                    alert_message = (
                        f"🚨 *CRITICAL RISK ALERT*\n\n"
                        f"🚢 *Vessel:* {v_id}\n"
                        f"📉 *Risk Score:* {risk}\n"
                        f"⚠️ *Status:* Immediate attention required."
                    )
                    await context.bot.send_message(
                        chat_id=chat_id, 
                        text=alert_message, 
                        parse_mode='Markdown'
                    )
                    sent_alerts.add(v_id)

        # Cleanup: Remove vessels from memory if their risk is resolved (drops below 0.8)
        sent_alerts = sent_alerts.intersection(current_high_risks)

    except Exception as error:
        print(f"Global Monitoring Error: {error}")

# 3. AI Assistant Logic (Chat Interaction)
# --- UPDATED AI ASSISTANT LOGIC (v9.6) ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = get_data()
        
        system_instruction = (
            "You are a Port Operations Expert. "
            "IMPORTANT: If 'delay_minutes' is empty, use the 'risk_score' to estimate potential delays. "
            "A high risk_score (above 0.8 or 80) implies a critical delay. "
            "When asked for a Top 10, group by Vessel ID to avoid showing the same ship multiple times. "
            "Respond concisely in English."
        )
        
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Dataset: {data}\nQuestion: {update.message.text}"}
            ]
        )
        
        await update.message.reply_text(completion.choices[0].message.content)
        
    except Exception as e:
        print(f"Chat Error: {e}")
        
# 4. Main Execution Engine
if __name__ == '__main__':
    print("🚢 SmartPort v9.5 - English Professional Engine Starting...")
    
    # Initialize the Telegram Application
    token = os.getenv("TELEGRAM_TOKEN")
    app = ApplicationBuilder().token(token).build()
    
    # Schedule the background task (Job Queue)
    # interval=60: Checks the Google Sheet every minute
    if app.job_queue:
        app.job_queue.run_repeating(check_vessel_risk, interval=60, first=10)
    else:
        print("Warning: JobQueue not initialized. Check if 'python-telegram-bot[job-queue]' is installed.")
    
    # Add handler for incoming chat messages
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    # Start the bot
    app.run_polling(drop_pending_updates=True)