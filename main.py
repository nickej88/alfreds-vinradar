import os
import requests
import schedule
import time
from bs4 import BeautifulSoup
from telegram import Bot

# =========================
# KONFIGURATION
# =========================

API_URL = "https://api-extern.systembolaget.se/sb-api-ecommerce/v1/productsearch/search"

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
]

seen_urls = set()

seen_wines = set()

URL = "https://www.systembolaget.se/nytt/om-vara-nyheter/lanseringar/"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

bot = Bot(token=TELEGRAM_TOKEN)

# =========================
# HUVUDFUNKTION
# =========================
def scan_systembolaget():

    print("🍷 Skannar via API...")

    try:
        
        params = {
            "page": 1,
            "size": 30,
            "sortBy": "Score",
            "sortDirection": "Ascending",
            "assortmentText": "Tillfälligt sortiment"
        }

        response = requests.get(
            API_URL,
            headers=HEADERS,
            params=params,
            timeout=20
        )

        data = response.json()

        print(data)

    except Exception as e:
        print(f"Fel: {e}")


def search_wines(search_term):

    url = f"https://www.systembolaget.se/sortiment/?text={search_term}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=20)

        if response.status_code == 200:

            return (
                f"🍷 Sökte efter: {search_term}\n\n"
                f"Öppna:\n{url}"
            )

        else:
            return "Systembolaget svarade inte korrekt, sir."

    except Exception as e:
        return f"Fel vid sökning: {e}"



# =========================
# SCHEMA
# =========================
schedule.every(3).hours.do(scan_systembolaget)
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

            if text.startswith("/search "):
                search_term = text.replace("/search ", "")

                result = search_wines(search_term)

                bot.send_message(
                chat_id=CHAT_ID,
                text=result
                )

            elif text.lower() == "vin":
               bot.send_message(
               chat_id=CHAT_ID,
               text="🍷 Alfred rapporterar: Vinradarn är aktiv, sir."
               )

            elif text.lower() == "scan":
               scan_systembolaget()

            else:
               bot.send_message(
               chat_id=CHAT_ID,
               text=f"Jag förstår inte kommandot: {text}"
               )
time.sleep(5)

while True:
    schedule.run_pending()
    check_messages()
    time.sleep(5)
