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
    "Azelia"
    "vin"
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

        found = []

        for producer in WATCHLIST:
            if producer.lower() in html:
                found.append(producer)

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

schedule.every(1).minutes.do(scan_systembolaget)
print("🍷 Alfreds Vinradar aktiv")

while True:
    schedule.run_pending()
    time.sleep(30)
