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

# --- FUNCIÓN QUE SUSTITUYE A n8n (Alertas Automáticas) ---
async def check_vessel_risk(context: ContextTypes.DEFAULT_TYPE):
    try:
        data = get_data()
        chat_id = os.getenv("TELEGRAM_CHAT_ID") # Añade tu Chat ID en el .env
        for vessel in data:
            if float(vessel.get('risk_score', 0)) > 0.8:
                msg = f"⚠️ ALERTA DE RIESGO: Buque {vessel['vessel_id']} está en {vessel['risk_score']}."
                await context.bot.send_message(chat_id=chat_id, text=msg)
    except Exception as e:
        print(f"Error en vigilancia: {e}")

# --- FUNCIÓN DE RESPUESTA (Chat) ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_data()
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "Experto portuario."},
                  {"role": "user", "content": f"Datos: {data}\nPregunta: {update.message.text}"}]
    )
    await update.message.reply_text(completion.choices[0].message.content)

if __name__ == '__main__':
    print("🚢 SmartPort v9.0 - Motor Unificado (Chat + Vigilancia)")
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
    
    # Programar la vigilancia cada 60 segundos
    app.job_queue.run_repeating(check_vessel_risk, interval=60, first=10)
    
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling(drop_pending_updates=True)