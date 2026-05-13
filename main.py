import os
import requests
import schedule
import time
from bs4 import BeautifulSoup
from telegram import Bot

# =========================
# KONFIGURATION
# =========================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

WATCHLIST = [
    "Vietti",
    "Massolino",
    "G.D. Vajra",
    "Produttori",
    "Le Ragnaie",
    "Il Poggione",
    "Guigal",
    "Beaucastel",
    "Charles Heidsieck",
    "Bollinger",
    "Fuligni",
    "Valdicava",
    "Azelia",
    "vin",
    "champagne",
]

URL = "https://www.systembolaget.se/nytt/om-vara-nyheter/lanseringar/"

bot = Bot(token=TELEGRAM_TOKEN)

# =========================
# HUVUDFUNKTION
# =========================

def scan_systembolaget():
    print("Skannar Systembolaget...")

    try:
        response = requests.get(URL, timeout=20)
        html = response.text.lower()
        
        print(html[:5000])
        
        found = []

        for producer in WATCHLIST:
            if producer.lower() in html:
                found.append(producer)
        
        print(found)

        if found:
            message = "🍷 Alfreds Vinradar\n\n"

            for wine in found:
                message += f"🔥 Intressant producent hittad: {wine}\n"

            message += "\nKolla Systembolaget direkt, sir."

            bot.send_message(chat_id=CHAT_ID, text=message)
            print("Notifiering skickad")

        else:
            print("Inget intressant idag")

    except Exception as e:
        print(f"Fel: {e}")

# =========================
# SCHEMA
# =========================
schedule.every().day.at("09:00").do(scan_systembolaget)
print("🍷 Alfreds Vinradar aktiv")

bot.send_message(chat_id=CHAT_ID, text="🍷 Alfreds Vinradar är online")

LAST_UPDATE_ID = None

def check_messages():
    global LAST_UPDATE_ID

    updates = bot.get_updates(offset=LAST_UPDATE_ID, timeout=10)

    for update in updates:
        LAST_UPDATE_ID = update.update_id + 1

        if update.message:
            text = update.message.text.lower()

            if text == "vin":
                bot.send_message(
                    chat_id=CHAT_ID,
                    text="🍷 Alfred rapporterar: Vinradarn är aktiv, sir."
                )

            elif text == "scan":
                scan_systembolaget()

            else:
                bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"Jag förstår inte kommandot: {text}"
                )
while True:
    schedule.run_pending()
    check_messages()
    time.sleep(5)
