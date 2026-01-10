import os
import json
import gspread
import asyncio
from openai import OpenAI
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from oauth2client.service_account import ServiceAccountCredentials

# 1. Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 2. Global state for alerts
sent_alerts = set()

def get_data():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # 1. Look for credentials in Railway Environment Variable
    google_json_str = os.getenv("GOOGLE_CREDENTIALS")
    
    if google_json_str:
        # If in Railway, parse the JSON string
        creds_dict = json.loads(google_json_str)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        # If in Local, use the physical file
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        
    gc = gspread.authorize(creds)
    # 2. Use the Spreadsheet ID from environment variables
    return gc.open_by_key(os.getenv("SPREADSHEET_ID")).sheet1.get_all_records()

# --- MONITORING (The Watchman - Optimized UX) ---
async def check_vessel_risk(context: ContextTypes.DEFAULT_TYPE):
    """
    Monitors high-risk vessels and sends a single consolidated alert 
    to avoid 'notification fatigue' and improve user experience.
    """
    global sent_alerts
    try:
        data = get_data()
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
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
        
        # --- CONSOLIDATED NOTIFICATION LOGIC ---
        if new_critical_ids:
            num_vessels = len(new_critical_ids)
            
            if num_vessels > 3:
                # If many vessels are at risk, send a summary
                message = (
                    f"🚨 *CRITICAL ALERT*: {num_vessels} new vessels with high risk detected!\n"
                    f"Check the dashboard or ask me: 'Which vessels are at risk?'"
                )
            else:
                # If only 1-3 vessels, list them specifically
                vessels_list = ", ".join([f"`{v}`" for v in new_critical_ids])
                message = f"🚨 *CRITICAL ALERT*: High risk detected in vessel(s): {vessels_list}."

            await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
        
        # Cleanup state: Only keep alerts for vessels that are still high risk
        sent_alerts = sent_alerts.intersection(current_high_risks)

    except Exception as e:
        if "timeout" in str(e).lower():
            print("⏳ Google Sheets API timeout - Skipping this cycle...")
        else:
            print(f"Monitor Error: {e}")

# --- ASSISTANT (The Analyst) ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = get_data()
        
        # We update the instruction to be bilingual while keeping the original business logic
        system_instruction = (
            "You are a Port Operations Analyst. "
            "Examine the dataset and list vessels by priority based on 'risk_score'. "
            "If the user asks for more vessels than available in the data, list all you have and "
            "mention that those are the only unique vessels currently tracked in the system. "
            "Identify the language used by the user (English or Spanish) and respond "
            "in that same language. Always maintain a professional and technical tone."
        )
        
        # User's query from Telegram
        user_query = update.message.text

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Dataset: {data}\nQuery: {user_query}"}
            ]
        )
        
        # Send the professional response back to the user
        await update.message.reply_text(completion.choices[0].message.content)

    except Exception as e:
        # In case of API errors or connectivity issues
        print(f"Chat Error: {e}")
        await update.message.reply_text("I am experiencing technical difficulties. Please try again in a moment.")

if __name__ == '__main__':
    print("🚢 SmartPort v9.7 - Final Cloud-Ready Polish")
    
    # Railway expects these to be set in the Variables tab
    token = os.getenv("TELEGRAM_TOKEN")
    
    app = ApplicationBuilder().token(token).build()
    
    if app.job_queue:
        # Check every 60 seconds
        app.job_queue.run_repeating(check_vessel_risk, interval=60, first=10)
    
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling(drop_pending_updates=True)