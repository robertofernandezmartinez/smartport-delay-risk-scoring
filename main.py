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

# Global state for alerts to avoid duplicate notifications
sent_alerts = set()

def get_data():
    """Fetches data from Google Sheets using environment credentials."""
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
        print(f"❌ Database Access Error: {e}")
        return []

# --- MONITORING (The Watchman) ---
async def check_vessel_risk(context: ContextTypes.DEFAULT_TYPE):
    global sent_alerts
    try:
        data = get_data()
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if not data or not chat_id: return

        current_high_risks = set()
        new_critical_alerts = []

        for vessel in data:
            # Match the column names from your Notifier script
            v_id = str(vessel.get('vessel_id', '')).strip()
            risk_level = str(vessel.get('risk_level', '')).strip()
            
            if not v_id: continue
            
            # Use the categorical 'risk_level' for the alert trigger
            # This is more reliable than checking the float score again
            if risk_level == 'CRITICAL':
                current_high_risks.add(v_id)
                if v_id not in sent_alerts:
                    new_critical_alerts.append(v_id)
                    sent_alerts.add(v_id)
        
        if new_critical_alerts:
            num = len(new_critical_alerts)
            # Professional message for the Port Authority
            msg = (
                f"🚨 *CRITICAL RISK ALERT*\n\n"
                f"The SmartPort AI has detected *{num} new vessels* with a high probability of delay.\n"
                f"Check the Operational Logs Dashboard for immediate action."
            )
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')
        
        # Reset memory: only keep alerts for vessels that are STILL critical
        sent_alerts = sent_alerts.intersection(current_high_risks)
        
    except Exception as e:
        print(f"Monitoring Loop Error: {e}")

# --- ASSISTANT (The Analyst) ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        ai_client = OpenAI(api_key=api_key)
        data = get_data()
        
        system_instruction = (
            "You are a Port Operations Analyst. Examine the dataset and provide insights. "
            "CRITICAL: Detect the language of the user's message and respond ALWAYS in that same language. "
            "If the user asks in Spanish, respond in Spanish. If English, respond in English. "
            "Maintain a professional and technical maritime tone. "
            "Be concise and provide direct actionable insights. Use bullet points for vessel lists and avoid conversational filler. Keep responses under 200 words unless technical detail is requested."
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
        print(f"Chat Response Error: {e}")
        await update.message.reply_text("I am currently unable to process your request.")

if __name__ == '__main__':
    print("🚢 SmartPort AI Deployment - Online")
    token = os.getenv("TELEGRAM_TOKEN")
    
    if token:
        # 1. Build the application
        app = ApplicationBuilder().token(token.strip()).build()
        
        # 2. Add handlers
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        
        # 3. Job Queue for alerts
        if app.job_queue:
            app.job_queue.run_repeating(check_vessel_risk, interval=60, first=10)
        
        # 4. START WITH EXTRA CLEANUP
        # 'drop_pending_updates=True' olvida mensajes antiguos
        # 'close_loop=True' asegura que al cerrar no queden hilos sueltos
        app.run_polling(drop_pending_updates=True, close_loop=True)