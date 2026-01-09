import os, gspread, asyncio
from openai import OpenAI
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from oauth2client.service_account import ServiceAccountCredentials

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Global set to track alerted vessels and avoid spam
sent_alerts = set()

def get_data():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    gc = gspread.authorize(creds)
    return gc.open_by_key(os.getenv("SPREADSHEET_ID")).sheet1.get_all_records()

# --- SMART MONITORING LOGIC (Anti-Spam) ---
async def check_vessel_risk(context: ContextTypes.DEFAULT_TYPE):
    global sent_alerts
    try:
        data = get_data()
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        current_high_risks = set()

        for vessel in data:
            v_id = str(vessel.get('vessel_id'))
            risk = float(vessel.get('risk_score', 0))
            
            if risk > 0.8:
                current_high_risks.add(v_id)
                # Only send message if it's a NEW risk alert
                if v_id not in sent_alerts:
                    message = (
                        f"🚨 *CRITICAL RISK ALERT*\n\n"
                        f"Vessel ID: {v_id}\n"
                        f"Risk Score: {risk}\n"
                        f"Action: Please check the Operations Dashboard."
                    )
                    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
                    sent_alerts.add(v_id)

        # Remove vessels from sent_alerts if their risk is no longer > 0.8
        sent_alerts = sent_alerts.intersection(current_high_risks)

    except Exception as error:
        print(f"Monitoring Error: {error}")

# --- AI ASSISTANT LOGIC ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_data()
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a Port Operations AI. Use the provided data to answer in English. Be technical and concise."},
            {"role": "user", "content": f"Dataset: {data}\nUser Query: {update.message.text}"}
        ]
    )
    await update.message.reply_text(completion.choices[0].message.content)

if __name__ == '__main__':
    print("🚢 SmartPort v9.4 - English Code / Spanish Support")
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
    
    # Run risk check every 60 seconds
    if app.job_queue:
        app.job_queue.run_repeating(check_vessel_risk, interval=60, first=10)
    
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling(drop_pending_updates=True)