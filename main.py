import os
import json
import gspread
import asyncio
from openai import OpenAI
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from oauth2client.service_account import ServiceAccountCredentials

# --- ROBUST ENVIRONMENT LOADING ---
# load_dotenv() is only for local dev. Railway uses its own Variables tab.
load_dotenv()

def get_env_variable(name):
    """Fetch variable from environment or print a clear error for Railway logs."""
    value = os.environ.get(name)
    if not value:
        print(f"❌ CRITICAL ERROR: Environment variable {name} is MISSING in Railway!")
    return value

# Get keys safely
OPENAI_KEY = get_env_variable("OPENAI_API_KEY")
TOKEN = get_env_variable("TELEGRAM_TOKEN")
SPREADSHEET_ID = get_env_variable("SPREADSHEET_ID")
CHAT_ID = get_env_variable("TELEGRAM_CHAT_ID")
GOOGLE_JSON_STR = os.environ.get("GOOGLE_CREDENTIALS")

# Initialize OpenAI only if key exists to prevent immediate crash
client = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None

# Global state for alerts
sent_alerts = set()

def get_data():
    """Connects to Google Sheets. Supports Cloud (env) and Local (file)."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        if GOOGLE_JSON_STR:
            creds_dict = json.loads(GOOGLE_JSON_STR)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        
        gc = gspread.authorize(creds)
        return gc.open_by_key(SPREADSHEET_ID).sheet1.get_all_records()
    except Exception as e:
        print(f"Database Error: {e}")
        return []

# --- MONITORING (The Watchman - Optimized UX) ---
async def check_vessel_risk(context: ContextTypes.DEFAULT_TYPE):
    global sent_alerts
    try:
        data = get_data()
        if not data or not CHAT_ID: return

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
            if num > 3:
                msg = f"🚨 *CRITICAL ALERT*: {num} new vessels with high risk detected!"
            else:
                vessels_str = ", ".join([f"`{i}`" for i in new_critical_ids])
                msg = f"🚨 *CRITICAL ALERT*: High risk in: {vessels_str}."
            await context.bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')
        
        sent_alerts = sent_alerts.intersection(current_high_risks)
    except Exception as e:
        if "timeout" not in str(e).lower(): print(f"Monitor Error: {e}")

# --- ASSISTANT (The Analyst) ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not client:
            await update.message.reply_text("❌ AI Error: OpenAI key missing in Railway variables.")
            return

        data = get_data()
        system_instruction = (
            "You are a Port Operations Analyst. Examine the dataset and list vessels by priority based on 'risk_score'. "
            "If the user asks for more vessels than available, list all you have. "
            "Identify the language used by the user (English or Spanish) and respond in that same language. "
            "Always maintain a professional and technical tone."
        )
        
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Dataset: {data}\nQuery: {update.message.text}"}
            ]
        )
        await update.message.reply_text(completion.choices[0].message.content, parse_mode='Markdown')
    except Exception as e:
        print(f"Chat Error: {e}")
        await update.message.reply_text("I'm having trouble analyzing the data right now.")

if __name__ == '__main__':
    print("🚢 SmartPort v9.7 - Final Cloud-Ready Polish")
    if not TOKEN:
        print("❌ ABORTING: No TELEGRAM_TOKEN found.")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        if app.job_queue:
            app.job_queue.run_repeating(check_vessel_risk, interval=60, first=10)
        
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        app.run_polling(drop_pending_updates=True)