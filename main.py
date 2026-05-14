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
]

seen_wines = set()

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
        soup = BeautifulSoup(response.text, "html.parser")

        links = soup.find_all("a")


        
        for link in links:

            href = link.get("href")

            if href and "/sortiment/" in href:

                 full_url = "https://www.systembolaget.se" + href

                 print(full_url)

                 try:
                     sub_response = requests.get(full_url, timeout=20)
                     sub_html = sub_response.text.lower()

                     for producer in WATCHLIST:

                        if producer.lower() in sub_html:

                            if producer not in seen_wines:

                                seen_wines.add(producer)

                                bot.send_message(
                                    chat_id=CHAT_ID,
                                    text=f"🍷 Alfred hittade {producer} i:\n{full_url}"
                                )

                 except Exception as e:
                     print(f"Fel på undersida: {e}")
            
       

def search_wines(search_term):

    url = f"https://www.systembolaget.se/sortiment/?text={search_term}"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)

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

while True:
    schedule.run_pending()
    check_messages()
    time.sleep(5)
