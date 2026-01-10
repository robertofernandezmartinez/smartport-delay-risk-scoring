import os
import json
import gspread
import asyncio
from openai import OpenAI
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from oauth2client.service_account import ServiceAccountCredentials

# 1. Load local env if exists
load_dotenv()

# Global state for alerts
sent_alerts = set()

def get_data():
    """Connects to Google Sheets using either local file or environment variable."""
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
        return gc.open_by_key(spreadsheet_id).sheet1.get_all_records()
    except Exception as e:
        print(f"❌ Database Error: {e}")
        return []

# --- MONITORING (The Watchman) ---
async def check_vessel_risk(context: ContextTypes.DEFAULT_TYPE):
    global sent_alerts
    try:
        data = get_data()
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if not data or not chat_id: return

        current_high_risks = set()
        new_critical_ids = []

        for vessel in data:
            v_id = str(vessel.get('vessel_id', '')).strip()
            if not v_id: continue
            try:
                risk = float(vessel.get('risk_score', 0))
            except: continue

            if risk > 0.8:
                current_high_risks.add(v_id)
                if v_id not in sent_alerts:
                    new_critical_ids.append(v_id)
                    sent_alerts.add(v_id)
        
        if new_critical_ids:
            num = len(new_critical_ids)
            msg = f"🚨 *CRITICAL ALERT*: {num} vessels with high risk!" if num > 3 else f"🚨 *CRITICAL ALERT*: High risk in: {', '.join(new_critical_ids)}"
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')
        
        sent_alerts = sent_alerts.intersection(current_high_risks)
    except Exception as e:
        print(f"Monitor Error: {e}")

# --- ASSISTANT (The Analyst) ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # We initialize OpenAI INSIDE the handler to prevent startup crashes
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            await update.message.reply_text("❌ Error: API Key not found in Railway.")
            return
            
        ai_client = OpenAI(api_key=api_key)
        data = get_data()
        
        system_instruction = (
            "You are a Port Operations Analyst. Examine the dataset and list vessels by priority. "
            "Respond in the same language as the user (English/Spanish). Professional tone."
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
        print(f"Chat Error: {e}")
        await update.message.reply_text("Technical error. Check logs.")

if __name__ == '__main__':
    print("🚢 SmartPort v9.8 - Fixed Startup Logic")
    token = os.getenv("TELEGRAM_TOKEN")
    
    if not token:
        print("❌ CRITICAL: TELEGRAM_TOKEN missing")
    else:
        app = ApplicationBuilder().token(token).build()
        if app.job_queue:
            app.job_queue.run_repeating(check_vessel_risk, interval=60, first=10)
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        app.run_polling(drop_pending_updates=True)