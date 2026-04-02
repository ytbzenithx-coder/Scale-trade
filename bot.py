import time
import pandas as pd
import requests
import os
from flask import Flask
from threading import Thread
from datetime import datetime

# --- CONFIGURATION ---
TOKEN = "8748658608:AAEBzyCtNKERBZ69HVnoP6CpQP1hPWdJwAI"
CHAT_ID = "8166605026"

ACTIFS = [
    "SOLUSDT", "PEPEUSDT", "WIFUSDT", "BONKUSDT", "FETUSDT", 
    "NEARUSDT", "RNDRUSDT", "ARBUSDT", "OPUSDT", "TIAUSDT", 
    "SUIUSDT", "INJUSDT", "STXUSDT", "LINKUSDT", "AVAXUSDT",
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT"
]

app = Flask('')

@app.route('/')
def home():
    return f"✅ SCALE-TRADE SÉCURISÉ - {datetime.now().strftime('%H:%M:%S')}"

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
        if not data or len(data) < 60: # Sécurité : il faut assez de données pour l'EMA50
            return None
        df = pd.DataFrame(data, columns=['ts','open','high','low','close','vol','ct','qv','nt','tb','tq','i'])
        df['close'] = df['close'].astype(float)
        return df
    except:
        return None

def monitor():
    time.sleep(10)
    send_telegram("🛰 **SCALE-TRADE RELANCÉ (MODE SÉCURISÉ)**\n_Protection contre les IndexErrors activée._")
    
    while True:
        print(f"--- Scan lancé à {datetime.now().strftime('%H:%M')} ---")
        for symbol in ACTIFS:
            df = fetch_data(symbol)
            
            # --- LA SÉCURITÉ ANTI-CRASH ---
            if df is None or df.empty:
                print(f"⚠️ Pas de données pour {symbol}, on passe au suivant.")
                continue
                
            try:
                df['ema'] = df['close'].ewm(span=50).mean()
                last = df.iloc[-1]
                prev = df.iloc[-2]
                
                if prev['close'] < prev['ema'] and last['close'] > last['ema']:
                    send_telegram(f"🟢 **ACHAT (LONG) : {symbol}**\nPrix : `{last['close']}`")
                elif prev['close'] > prev['ema'] and last['close'] < last['ema']:
                    send_telegram(f"🔴 **VENTE (SHORT) : {symbol}**\nPrix : `{last['close']}`")
            except Exception as e:
                print(f"❌ Erreur sur {symbol}: {e}")
        
        time.sleep(600)

if __name__ == "__main__":
    t = Thread(target=monitor, daemon=True)
    t.start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
