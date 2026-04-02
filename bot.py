import os
import asyncio
import requests
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from telegram.ext import Application
from flask import Flask
from threading import Thread

# --- SERVEUR FLASK ---
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Scale-Trade Elite Secure is live!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host='0.0.0.0', port=port)

# --- CONFIG ---
TOKEN = "8748658608:AAEBzyCtNKERBZ69HVnoP6CpQP1hPWdJwAI"
ADMIN_ID = 8166605026

MARCHES = [
    "SOLUSDT", "PEPEUSDT", "WIFUSDT", "BONKUSDT", "FETUSDT", 
    "NEARUSDT", "RNDRUSDT", "ARBUSDT", "OPUSDT", "TIAUSDT", 
    "SUIUSDT", "INJUSDT", "STXUSDT", "LINKUSDT", "AVAXUSDT",
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT"
]

deja_alerte = {}

def analyze_market(symbol):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=15m&limit=60"
        r = requests.get(url, timeout=5).json()
        df = pd.DataFrame(r, columns=['OT','O','H','L','C','V','CT','QV','NT','TB','TQ','I'])
        
        # Données numériques
        prices = df['C'].astype(float).values
        volumes = df['V'].astype(float).values
        
        # --- BARRIÈRE 1 : IA (MACHINE LEARNING) ---
        returns = np.diff(prices) / prices[:-1]
        X, y = returns[:-1].reshape(-1, 1), (returns[1:] > 0).astype(int)
        model = LogisticRegression().fit(X, y)
        prob = model.predict_proba(np.array([[returns[-1]]]))[0][1] * 100
        
        # --- BARRIÈRE 2 : CONFIRMATION VOLUME ---
        # On vérifie si le volume actuel est > 1.2x la moyenne des 10 derniers
        avg_vol = np.mean(volumes[-11:-1])
        vol_confirmed = volumes[-1] > (avg_vol * 1.1)
        
        return round(prob, 1), prices[-1], vol_confirmed
    except:
        return 50.0, 0, False

async def run_scan(app: Application):
    await app.bot.send_message(ADMIN_ID, "🛡️ **SCALE-TRADE : MODE SÉCURISÉ ACTIVÉ**\n_IA 65% + Filtre Volume 1.1x_")
    
    while True:
        for symbol in MARCHES:
            score, prix, vol_ok = analyze_market(symbol)
            if prix == 0: continue
            
            is_buy = score >= 50
            final_score = score if is_buy else round(100 - score, 1)
            side = "🟢 BUY" if is_buy else "🔴 SELL"

            # FILTRE STRICT : Score >= 65% ET Volume confirmé
            if final_score >= 65 and vol_ok:
                if deja_alerte.get(symbol) != "ELITE":
                    move = prix * 0.012 # 1.2% de mouvement estimé
                    if is_buy:
                        tp, sl = prix + move, prix - (move * 0.8)
                    else:
                        tp, sl = prix - move, prix + (move * 0.8)
                    
                    msg = (f"🔥 **SIGNAL ÉLITE SÉCURISÉ**\n"
                           f"💎 `{symbol}` | Force: `{final_score}%`\n\n"
                           f"Action: **{side}**\n"
                           f"🎯 TP: `{tp:.4f}`\n"
                           f"🛡️ SL: `{sl:.4f}`\n\n"
                           f"⚡ **EXÉCUTION IMMÉDIATE !**")
                    
                    await app.bot.send_message(ADMIN_ID, msg, parse_mode='Markdown')
                    deja_alerte[symbol] = "ELITE"
            
            # Reset si la force chute pour permettre un futur signal
            if final_score < 58:
                deja_alerte[symbol] = None
                
            await asyncio.sleep(0.4)
        await asyncio.sleep(60)

async def main():
    Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    await app.initialize()
    asyncio.create_task(run_scan(app))
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    while True: await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
