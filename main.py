import os, gspread, asyncio
from openai import OpenAI
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from oauth2client.service_account import ServiceAccountCredentials

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_data():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    gc = gspread.authorize(creds)
    return gc.open_by_key(os.getenv("SPREADSHEET_ID")).sheet1.get_all_records()

# --- AUTOMATED ALERTS (Replaces n8n) ---
async def check_vessel_risk(context: ContextTypes.DEFAULT_TYPE):
    try:
        data = get_data()
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        for vessel in data:
            # We assume your column name is 'risk_score'
            risk = float(vessel.get('risk_score', 0))
            if risk > 0.8:
                msg = f"⚠️ RISK ALERT: Vessel {vessel['vessel_id']} reported with a score of {risk}. Immediate action required."
                await context.bot.send_message(chat_id=chat_id, text=msg)
    except Exception as e:
        print(f"Monitoring Error: {e}")

# --- CHAT INTERACTION ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_data()
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a Port Operations AI Expert. Answer briefly and professionally in English based on the provided data."},
            {"role": "user", "content": f"Context Data: {data}\nUser Query: {update.message.text}"}
        ]
    )
    await update.message.reply_text(completion.choices[0].message.content)

if __name__ == '__main__':
    print("🚢 SmartPort v9.1 - Unified Engine (Chat + Monitoring)")
    # We initialize the app with the JobQueue support
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
    
    # Check for risks every 60 seconds
    if app.job_queue:
        app.job_queue.run_repeating(check_vessel_risk, interval=60, first=10)
    
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling(drop_pending_updates=True)