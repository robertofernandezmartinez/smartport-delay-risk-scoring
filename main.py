import os
import json
import gspread
import asyncio
from openai import OpenAI
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from oauth2client.service_account import ServiceAccountCredentials

# 1. Load local env if exists (for Local Dev)
load_dotenv()

# Global state for alerts
sent_alerts = set()

def get_data():
    """Connects to Google Sheets using either Railway Env Var or credentials.json."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    google_json_str = os.getenv("GOOGLE_CREDENTIALS")
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    
    if not spreadsheet_id:
        print("❌ SPREADSHEET_ID is missing!")
        return []

    try:
        if google_json_str:
            # Cloud Path
            creds_dict = json.loads(google_json_str)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            # Local Path
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        
        gc = gspread.authorize(creds)
        # We ensure it opens the first sheet correctly
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
        
        # Guard clause: stop if no data or no chat_id
        if not data or not chat_id:
            return

        current_high_risks = set()
        new_critical_ids = []

        for vessel in data:
            v_id = str(vessel.get('vessel_id', '')).strip()
            if not v_id: continue
            
            try:
                risk = float(vessel.get('risk_score', 0))
            except (ValueError, TypeError):
                continue

            if risk > 0.8:
                current_high_risks.add(v_id)
                if v_id not in sent_alerts:
                    new_critical_ids.append(v_id)
                    sent_alerts.add(v_id)
        
        # Notification logic
        if new_critical_ids:
            num = len(new_critical_ids)
            if num > 3:
                msg = f"🚨 *CRITICAL ALERT*: {num} new vessels with high risk detected!"
            else:
                # Formatting IDs with backticks for professional look
                vessels_str = ", ".join([f"`{v}`" for v in new_critical_ids])
                msg = f"🚨 *CRITICAL ALERT*: High risk in: {vessels_str}."
            
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')
        
        # Cleanup state
        sent_alerts = sent_alerts.intersection(current_high_risks)
        
    except Exception as e:
        # Ignore common timeout errors in logs to keep them clean
        if "timeout" not in str(e).lower():
            print(f"Monitor Error: {e}")

# --- ASSISTANT (The Analyst) ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            await update.message.reply_text("❌ Error: OpenAI API Key not found in Railway.")
            return
            
        ai_client = OpenAI(api_key=api_key)
        data = get_data()
        
        if not data:
            await update.message.reply_text("I can't access the port data right now.")
            return

        system_instruction = (
            "You are a Port Operations Analyst. Examine the dataset and list vessels by priority "
            "based on 'risk_score'. If the user asks for more vessels than available, list all you have. "
            "CRITICAL: Respond in the same language as the user (English or Spanish). Professional tone."
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
        await update.message.reply_text("Technical error. Please try again later.")

if __name__ == '__main__':
    print("🚢 SmartPort v9.9 - Final Stable Build")
    
    # We strip any weird character like '}' or spaces from the token
    raw_token = os.getenv("TELEGRAM_TOKEN")
    token = raw_token.strip().replace('}', '') if raw_token else None
    
    if not token:
        print("❌ CRITICAL: TELEGRAM_TOKEN missing")
        # List keys to help debugging in logs
        print(f"Available env keys: {list(os.environ.keys())}")
    else:
        app = ApplicationBuilder().token(token).build()
        
        # Configure the job queue for the Watchman
        if app.job_queue:
            app.job_queue.run_repeating(check_vessel_risk, interval=60, first=10)
        
        # Handlers
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        
        print("✅ Bot is online and monitoring. Ready for Telegram messages.")
        app.run_polling(drop_pending_updates=True)