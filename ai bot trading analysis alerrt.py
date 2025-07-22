import time
import pandas as pd
import requests
from binance.spot import Spot
import ta

# Binance Testnet Credentials
API_KEY = "lRcq9kfcHZIxyHhAX22js2SRKJC971pxmR8tgnNGhgzjTEDOMSPKZHRhBXP2ap3s"
API_SECRET = "gmiDhmAXQK3b6UYwzRcm37ARMZxe5CcpOfSntjrAfVSlqM4UwiChUzwQ9KlgI20C"
client = Spot(api_key=API_KEY, api_secret=API_SECRET, base_url="https://testnet.binance.vision")

# Telegram Bot Credentials
TELEGRAM_TOKEN = "8094958698:AAHxPb8LXphAskerDlbZUDenZgtv8xwQij4"
CHAT_ID = "6990265255"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("✅ Telegram alert sent!")
    else:
        print("❌ Failed to send alert:", response.text)

def get_klines(symbol="BTCUSDT", interval="5m", limit=100):
    raw_klines = client.klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(raw_klines, columns=[
        "time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "num_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    df["time"] = pd.to_datetime(df["time"], unit='ms')
    df.set_index("time", inplace=True)
    df["close"] = df["close"].astype(float)
    return df[["close"]]

def add_indicators(df):
    df["SMA_20"] = ta.trend.sma_indicator(df["close"], window=20)
    df["RSI_14"] = ta.momentum.RSIIndicator(df["close"], window=14).rsi()
    return df

def check_signal(df):
    last_rsi = df["RSI_14"].iloc[-1]
    last_price = df["close"].iloc[-1]
    sma = df["SMA_20"].iloc[-1]
    print(f"🔎 RSI: {last_rsi:.2f}, Price: {last_price:.2f}, SMA: {sma:.2f}")  # Debug info

    signal = None

    # TEMPORARY: relax conditions for testing
    if last_rsi < 50 and last_price > sma:
        signal = f"📈 TEST BUY Signal → RSI={last_rsi:.2f}, Price={last_price:.2f}, SMA={sma:.2f}"
    elif last_rsi > 50 and last_price < sma:
        signal = f"📉 TEST SELL Signal → RSI={last_rsi:.2f}, Price={last_price:.2f}, SMA={sma:.2f}"

    return signal


# === Main Loop ===
while True:
    try:
        df = get_klines()
        df = add_indicators(df)
        signal = check_signal(df)

        if signal:
            print("📣 ALERT:", signal)
            send_telegram(f"🚨 Trade Signal:\n{signal}")
        else:
            print("✅ No signal at the moment.")

    except Exception as e:
        print("⚠️ Error:", str(e))

    # Wait for  1 min (60 seconds)
    time.sleep(60)
