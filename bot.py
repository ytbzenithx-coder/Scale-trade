import time
import pandas as pd
import requests
import os
from flask import Flask
from threading import Thread
from datetime import datetime

# --- CONFIGURATION (Tes infos) ---
TOKEN = "8748658608:AAEBzyCtNKERBZ69HVnoP6CpQP1hPWdJwAI"
CHAT_ID = "8166605026"

# 15 Haut Rendement + 5 Stables
ACTIFS = [
    "SOLUSDT", "PEPEUSDT", "WIFUSDT", "BONKUSDT", "FETUSDT", 
    "NEARUSDT", "RNDRUSDT", "ARBUSDT", "OPUSDT", "TIAUSDT", 
    "SUIUSDT", "INJUSDT", "STXUSDT", "LINKUSDT", "AVAXUSDT",
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT"
]

app = Flask('')

@app.route('/')
def home():
    return f"✅ SCALE-TRADE LIVE - {datetime.now().strftime('%H:%M:%S')}"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except:
        pass

def fetch_data(symbol):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=15m&limit=100"
    try:
        data = requests.get(url, timeout=10).json()
        df = pd.DataFrame(data, columns=['ts','open','high','low','close','vol','ct','qv','nt','tb','tq','i'])
        df['close'] = df['close'].astype(float)
        return df
    except:
        return None

def monitor():
    # Petit délai de sécurité au lancement
    time.sleep(10)
    send_telegram("🛰 **SCALE-TRADE INITIALISÉ**\n_Surveillance de 20 marchés activée (10 min)_")
    
    while True:
        for symbol in ACTIFS:
            df = fetch_data(symbol)
            if df is not None:
                # Indicateur de Tendance EMA50 (Le plus fiable de tes tests)
                df['ema'] = df['close'].ewm(span=50).mean()
                last = df.iloc[-1]
                prev = df.iloc[-2]
                
                # Signal de croisement
                if prev['close'] < prev['ema'] and last['close'] > last['ema']:
                    send_telegram(f"🟢 **SIGNAL ACHAT (LONG) : {symbol}**\nPrix : `{last['close']}`")
                elif prev['close'] > prev['ema'] and last['close'] < last['ema']:
                    send_telegram(f"🔴 **SIGNAL VENTE (SHORT) : {symbol}**\nPrix : `{last['close']}`")
        
        # Pause de 10 minutes entre chaque scan complet
        time.sleep(600)

if __name__ == "__main__":
    # Lancement du moteur de scan dans un thread séparé
    t = Thread(target=monitor, daemon=True)
    t.start()
    
    # Lancement du serveur Web pour Render
    port = int(os.environ.get("PORT", 8080))
    print(f"🌐 Serveur Web démarré sur le port {port}")
    app.run(host='0.0.0.0', port=port)
