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