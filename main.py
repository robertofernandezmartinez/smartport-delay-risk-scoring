import os
import json
import gspread
import asyncio
from openai import OpenAI
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from oauth2client.service_account import ServiceAccountCredentials

# 1. Environment Loading
load_dotenv()

# Global state to ensure single responses
processed_updates = set()
sent_alerts = set()

def get_data():
    """Accesses Google Sheets using service account credentials."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    google_json_str = os.getenv("GOOGLE_CREDENTIALS")
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    
    try:
        if google_json_str:
            creds_dict = json.loads(google_json_str)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        
        gc = gspread.authorize(creds)
        return gc.open_by_key(spreadsheet_id).worksheet("risk_alerts").get_all_records()
    except Exception as e:
        print(f"❌ Database Connectivity Error: {e}")
        return []

# --- RISK MONITORING SYSTEM ---
async def check_vessel_risk(context: ContextTypes.DEFAULT_TYPE):
    global sent_alerts
    try:
        data = get_data()
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if not data or not chat_id: return

        current_high_risks = set()
        new_alerts = []

        for vessel in data:
            v_id = str(vessel.get('vessel_id', '')).strip()
            risk = str(vessel.get('risk_level', '')).strip()
            
            if risk == 'CRITICAL':
                current_high_risks.add(v_id)
                if v_id not in sent_alerts:
                    new_alerts.append(v_id)
                    sent_alerts.add(v_id)
        
        if new_alerts:
            msg = f"🚨 *CRITICAL RISK*: SmartPort AI detected {len(new_alerts)} vessels requiring immediate attention."
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')
        
        sent_alerts = sent_alerts.intersection(current_high_risks)
    except Exception as e:
        print(f"Monitoring Error: {e}")

# --- AI LOGISTICS ANALYST ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global processed_updates
    
    # DEDUPLICATION: Ensures only one response per message ID
    if not update.message or update.message.message_id in processed_updates:
        return
    
    processed_updates.add(update.message.message_id)

    try:
        ai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        data = get_data()
        
        system_instruction = (
            "You are a Port Operations Analyst. Analyze the dataset and provide insights. "
            "Respond in the same language as the user. "
            "Be direct, professional, and concise. Use bullet points for vessel lists."
        )
        
        completion = ai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Dataset: {data}\nQuery: {update.message.text}"}
            ]
        )
        await update.message.reply_text(completion.choices[0].message.content, parse_mode='Markdown')
    except Exception as e:
        print(f"AI Assistant Error: {e}")
    finally:
        # Keep internal memory clean
        if len(processed_updates) > 50:
            processed_updates.clear()

if __name__ == '__main__':
    print("🚢 SmartPort AI Deployment - Online (New Token Active)")
    token = os.getenv("TELEGRAM_TOKEN")
    
    if token:
        app = ApplicationBuilder().token(token.strip()).build()
        
        # Reset Session
        loop = asyncio.get_event_loop()
        loop.run_until_complete(app.bot.delete_webhook(drop_pending_updates=True))
        
        if app.job_queue:
            app.job_queue.run_repeating(check_vessel_risk, interval=60, first=10)
        
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        app.run_polling(drop_pending_updates=True)