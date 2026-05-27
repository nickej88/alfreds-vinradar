import os
import requests
import schedule
import time
from telegram import Bot
import json

# =========================
# KONFIGURATION
# =========================

API_URL = "https://api-extern.systembolaget.se/sb-api-ecommerce/v1/productsearch/search"

API_KEY = os.getenv("SB_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

WATCHLIST = [
    "Vietti",

]

PAGE_SIZE = 30
SORT_BY = "Score"
SORT_DIRECTION = "Descending"
ASSORTMENT = "Tillfälligt sortiment"


seen_wines = set()

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Ocp-Apim-Subscription-Key": API_KEY
}


# =========================
# HUVUDFUNKTION
# =========================
def scan_systembolaget():
    
    print("🍷 Skannar via API...")

    try:
        first_params = {
            "page": 1,
            "size": PAGE_SIZE,
            "sortBy": SORT_BY,
            "sortDirection": SORT_DIRECTION,
            "assortmentText": ASSORTMENT,
        }

        first_response = requests.get(
            API_URL,
            headers=HEADERS,
            params=first_params,
            timeout=20
        )

        first_data = first_response.json()

        total_pages = first_data["metadata"]["totalPages"]

        print(f"🍷 Hittade {total_pages} sidor")

        for page in range(1, total_pages + 1):     
        
            params = {
                "page": page,
                "size": PAGE_SIZE,
                "sortBy": SORT_BY,
                "sortDirection": SORT_DIRECTION,
                "assortmentText": ASSORTMENT
            }

            response = requests.get(
                API_URL,
                headers=HEADERS,
                params=params,
                timeout=20
            )

            data = response.json()

            print(f"🍷 Sida {page}")
            
            products = data["products"]

            for product in products:

                category = product.get("categoryLevel1")

                if product.get("isDiscontinued"):
                    continue

                if product.get("isCompletelyOutOfStock"):
                    continue

                if category != "Vin":
                    continue

                producer = product.get("producerName", "Okänd producent")
                wine_name = product["productNameBold"]
                vintage = product.get("vintage") or "NV"
                price = product["price"]
                launch_date = product["productLaunchDate"]
                launch_date = launch_date.split("T")[0]

                for watch in WATCHLIST:

                    if (
                        watch.lower() in producer.lower()
                        or
                        watch.lower() in wine_name.lower()
                    ):
                    
                        wine_id = f"{producer}-{wine_name}-{vintage}"

                        if wine_id in seen_wines:
                            continue

                        seen_wines.add(wine_id)
                    
                        bot.send_message(
                            chat_id=CHAT_ID,
                            text=(
                                f"🍷 Alfred hittade något intressant\n\n"
                                f"Producent: {producer}\n"
                                f"Vin: {wine_name}\n"
                                f"Årgång: {vintage}\n"
                                f"Pris: {price} kr\n"
                                f"Släpp: {launch_date}"
                            )
                        )

                        print(
                            f"{producer} | "
                            f"{wine_name} | "
                            f"{vintage} | "
                            f"{price} kr | "
                            f"{launch_date}"
                        )
                    
            time.sleep(1)
    
    except Exception as e:
        print(f"Fel: {e}")


def add_watch(search_term):

    if search_term not in WATCHLIST:
        WATCHLIST.append(search_term)
        save_watchlist()
        return f"🍷 Tillagd i watchlist: {search_term}"

    return f"🍷 {search_term} finns redan i watchlist."


def remove_watch(search_term):

    if search_term in WATCHLIST:
        WATCHLIST.remove(search_term)
        save_watchlist()
        return f"🍷 Borttagen från watchlist: {search_term}"
            
    return f"🍷 Hittade inte {search_term} i watchlist."


def show_watchlist():

    if not WATCHLIST:
        return "🍷 Watchlist är tom, sir."

    message = "🍷 Watchlist:\n\n"

    for watch in WATCHLIST:
        message += f"• {watch}\n"

    return message

def save_watchlist():

    with open("watchlist.json", "w") as file:
        json.dump(WATCHLIST, file)

def load_watchlist():

    global WATCHLIST

    try:

        with open("watchlist.json", "r") as file:
            WATCHLIST = json.load(file)

    except FileNotFoundError:

        save_watchlist()

def search_wines(search_term):   
 
    params = {
        "page": 1,
        "size": 10,
        "sortBy": "Score",
        "sortDirection": "Ascending",
        "textQuery": search_term
    }

    try:

        response = requests.get(
            API_URL,
            headers=HEADERS,
            params=params,
            timeout=20
        )

        data = response.json()

        products = data["products"]

        if not products:
            return "🍷 Alfred hittade inget, sir."

        message = "🍷 Alfred hittade:\n\n"

        for product in products:

            category = product.get("categoryLevel1")

            if product.get("isDiscontinued"):
                continue

            if product.get("isCompletelyOutOfStock"):
                continue

            if category != "Vin":
                continue

            producer = product.get("producerName", "Okänd producent")
            wine_name = product.get("productNameBold")
            vintage = product.get("vintage") or "NV"
            price = product.get("price")
            product_number = product["productNumber"]
            product_url = (
            "https://www.systembolaget.se/sortiment/?q="
            f"{product_number}"
            )
    
            message += (
                f"🍷 {wine_name} {vintage}\n"
                f"{price} kr\n"
                f"🔗 {product_url}\n\n"
                
            )

        return message

    except Exception as e:
        return f"Fel vid sökning: {e}"



load_watchlist()

bot = Bot(token=TELEGRAM_TOKEN)
bot.delete_webhook(drop_pending_updates=True)


# =========================
# SCHEMA
# =========================
schedule.every().day.at("08:00").do(scan_systembolaget)
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

            elif text.startswith("/add "):

                search_term = text.replace("/add ", "")

                result = add_watch(search_term)

                bot.send_message(
                    chat_id=CHAT_ID,
                    text=result
                )

            elif text.startswith("/remove "):

                search_term = text.replace("/remove ", "")

                result = remove_watch(search_term)

                bot.send_message(
                    chat_id=CHAT_ID,
                    text=result
                )

            elif text == "/watchlist":

                result = show_watchlist()

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

time.sleep(15)

scan_systembolaget()

while True:
    schedule.run_pending()
    check_messages()
    time.sleep(15)
