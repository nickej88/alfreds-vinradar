import os
import requests
import schedule
import time
from telegram import Bot
import telegram.error
import json
import sqlite3

# =========================
# KONFIGURATION
# =========================

API_URL = "https://api-extern.systembolaget.se/sb-api-ecommerce/v1/productsearch/search"

API_KEY = os.getenv("SB_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

PAGE_SIZE = 30
SORT_BY = "Score"
SORT_DIRECTION = "Descending"
ASSORTMENT = "Tillfälligt sortiment"

WINE_CATEGORY = "Vin"

SEARCH_SIZE = 50
SEARCH_SORT_DIRECTION = "Ascending"



HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Ocp-Apim-Subscription-Key": API_KEY
}


# =========================
# SQLITE
# =========================

connection = sqlite3.connect("winebot.db")
cursor = connection.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    watch_type TEXT,
    watch_value TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS seen_wines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wine_id TEXT UNIQUE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producer TEXT,
    wine TEXT,
    vintage TEXT,
    price REAL,
    country TEXT,
    region TEXT,
    grape TEXT,
    style TEXT
)
""")

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print(cursor.fetchall())

connection.commit()
print("🍷 SQLite-databas redo")


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
        
        all_products = []
        
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
            all_products.extend(products)
            
            for product in products:

                category = product.get("categoryLevel1")

                if product.get("isDiscontinued"):
                    continue

                if product.get("isCompletelyOutOfStock"):
                    continue

                if category != WINE_CATEGORY:
                    continue
       
                launch_date = product["productLaunchDate"]
                launch_date = launch_date.split("T")[0]

                producer = product.get("producerName", "Okänd producent")
                wine = product.get("productNameBold")
                vintage = product.get("vintage") or "NV"
                price = product.get("price")
                product_number = product["productNumber"]
                product_url = f"https://www.systembolaget.se/sortiment/?q={product_number}"    
                origin_level_1 = product.get("originLevel1")
                region = product.get("originLevel2")
                style = product.get("categoryLevel2")
                profile = product.get("categoryLevel3")
                country = product.get("country")
                grape = product.get("grapes")
                if isinstance(grape, list):
                    grape = ", ".join(grape)
                    
                save_product_sql(
                    producer,
                    wine,
                    vintage,
                    price,
                    country,
                    region,
                    grape,
                    style
                )

                watchlist = load_watchlist_sql()
                
                for watch in watchlist:

                    watch_type, watch_value = watch.split(":")

                    if (
                        watch_type == "producer"
                        and
                        watch_value in producer.lower()
                    ):

                        wine_id = f"{producer}-{wine}-{vintage}"

                        if wine_seen(wine_id):
                            continue

                        save_seen_wine(wine_id)            
                    
                        bot.send_message(
                            chat_id=CHAT_ID,
                            text=(
                                f"🍷 Alfred hittade något intressant\n\n"
                                f"Producent: {producer}\n"
                                f"Vin: {wine}\n"
                                f"Årgång: {vintage}\n"
                                f"Pris: {price} kr\n"
                                f"Släpp: {launch_date}"
                            )
                        )

                    elif (
                        watch_type == "wine"
                        and
                        watch_value in wine.lower()
                    ):

                        wine_id = f"{producer}-{wine}-{vintage}"

                        if wine_seen(wine_id):
                            continue

                        save_seen_wine(wine_id)

                        bot.send_message(
                            chat_id=CHAT_ID,
                            text=(
                                f"🍷 Alfred hittade något intressant\n\n"
                                f"Producent: {producer}\n"
                                f"Vin: {wine}\n"
                                f"Årgång: {vintage}\n"
                                f"Pris: {price} kr\n"
                                f"Släpp: {launch_date}"
                            )
                        )
                  
                    elif (
                        watch_type == "region"
                        and
                        region
                        and
                        watch_value in region.lower()
                    ):

                        wine_id = f"{producer}-{wine}-{vintage}"

                        if wine_seen(wine_id):
                            continue

                        save_seen_wine(wine_id)               

                        bot.send_message(
                            chat_id=CHAT_ID,
                            text=(
                                f"🍷 Alfred hittade något intressant\n\n"
                                f"Producent: {producer}\n"
                                f"Vin: {wine}\n"
                                f"Årgång: {vintage}\n"
                                f"Pris: {price} kr\n"
                                f"Släpp: {launch_date}"
                            )
                        )

                    elif (
                        watch_type == "country"
                        and
                        country
                        and
                        watch_value in country.lower()
                    ):

                        wine_id = f"{producer}-{wine}-{vintage}"

                        if wine_seen(wine_id):
                            continue

                        save_seen_wine(wine_id)                        

                        bot.send_message(
                            chat_id=CHAT_ID,
                            text=(
                                f"🍷 Alfred hittade något intressant\n\n"
                                f"Producent: {producer}\n"
                                f"Vin: {wine}\n"
                                f"Årgång: {vintage}\n"
                                f"Pris: {price} kr\n"
                                f"Släpp: {launch_date}"
                            )
                        )
                    
                    elif (
                        watch_type == "grape"
                        and
                        grape
                        and
                        watch_value in grape.lower()
                        ):

                        wine_id = f"{producer}-{wine}-{vintage}"

                        if wine_seen(wine_id):
                            continue

                        save_seen_wine(wine_id)                        

                        bot.send_message(
                            chat_id=CHAT_ID,
                            text=(
                                f"🍷 Alfred hittade något intressant\n\n"
                                f"Producent: {producer}\n"
                                f"Vin: {wine}\n"
                                f"Årgång: {vintage}\n"
                                f"Pris: {price} kr\n"
                                f"Släpp: {launch_date}"
                            )
                        )

                    elif (
                        watch_type == "style"
                        and
                        style
                        and
                        watch_value in style.lower()
                    ):                   
                        wine_id = f"{producer}-{wine}-{vintage}"

                        if wine_seen(wine_id):
                            continue

                        save_seen_wine(wine_id)
                    
                        bot.send_message(
                            chat_id=CHAT_ID,
                            text=(
                                f"🍷 Alfred hittade något intressant\n\n"
                                f"Producent: {producer}\n"
                                f"Vin: {wine}\n"
                                f"Årgång: {vintage}\n"
                                f"Pris: {price} kr\n"
                                f"Släpp: {launch_date}"
                            )
                        )               
                    
            time.sleep(0.2)

        save_products(all_products)
    
    except Exception as e:
        print(f"Fel: {e}")


def scan_local_products():

    products = load_products_sql()

    print(f"🍷 Lokal SQL-scan: {len(products)} produkter")


def load_products():

    try:

        with open("products.json", "r") as file:
            return json.load(file)

    except FileNotFoundError:

        return []

def save_products(products):

    with open("products.json", "w") as file:
        json.dump(products, file)

    print("🍷 Products sparade")

def load_products_sql():

    cursor.execute("""
    SELECT
        producer,
        wine,
        vintage,
        price,
        country,
        region,
        grape,
        style
    FROM products
    """)

    return cursor.fetchall()

def load_watchlist_sql():

    cursor.execute("""
    SELECT watch_type, watch_value
    FROM watchlist
    """)

    rows = cursor.fetchall()

    return [
        f"{watch_type}:{watch_value}"
        for watch_type, watch_value in rows
    ]

def add_watch_sql(search_term):

    watch_type, watch_value = search_term.split(":")

    cursor.execute("""
    INSERT INTO watchlist (
        watch_type,
        watch_value
    )
    VALUES (?, ?)
    """, (watch_type, watch_value))

    connection.commit()

def wine_seen(wine_id):

    cursor.execute("""
    SELECT wine_id
    FROM seen_wines
    WHERE wine_id = ?
    """, (wine_id,))

    return cursor.fetchone() is not None

def save_seen_wine(wine_id):

    cursor.execute("""
    INSERT OR IGNORE INTO seen_wines (
        wine_id
    )
    VALUES (?)
    """, (wine_id,))

    connection.commit()

def save_product_sql(
    producer,
    wine,
    vintage,
    price,
    country,
    region,
    grape,
    style
):

    cursor.execute("""
    INSERT INTO products (
        producer,
        wine,
        vintage,
        price,
        country,
        region,
        grape,
        style
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        producer,
        wine,
        vintage,
        price,
        country,
        region,
        grape,
        style
    ))

    connection.commit()

def show_watchlist():

    watchlist = load_watchlist_sql()

    if not watchlist:
        return "🍷 Watchlist är tom, sir."

    message = "🍷 Watchlist:\n\n"

    for watch in watchlist:

        watch_type, watch_value = watch.split(":")

        if watch_type == "producer":
            message += f"🍷 Producent: {watch_value}\n"

        elif watch_type == "wine":
            message += f"🍷 Vin: {watch_value}\n"

        elif watch_type == "region":
            message += f"🍷 Region: {watch_value}\n"

        elif watch_type == "country":
            message += f"🌍 Land: {watch_value}\n"

        elif watch_type == "grape":
            message += f"🍇 Druva: {watch_value}\n"

        elif watch_type == "style":
            message += f"🍷 Stil: {watch_value}\n"

    return message

def search_wines(search_term):   
    
    params = {
        "page": 1,
        "size": SEARCH_SIZE,
        "sortBy": "Score",
        "sortDirection": SEARCH_SORT_DIRECTION,
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

            #if product.get("isBsAssortment"):
            #    continue

            if category != WINE_CATEGORY:
                continue

            producer = product.get("producerName", "Okänd producent")
            wine = product.get("productNameBold")
            vintage = product.get("vintage") or "NV"
            price = product.get("price")
            product_number = product["productNumber"]
            product_url = f"https://www.systembolaget.se/sortiment/?q={product_number}"    
            origin_level_1 = product.get("originLevel1")
            region = product.get("originLevel2")
            style = product.get("categoryLevel2")
            profile = product.get("categoryLevel3")
            country = product.get("country")
            grape = product.get("grapes")
            

            #     print(
            #        f"{wine} | "
            #        f"{style} | "
            #        f"{category_3}"
            #    )
    
            message += (
                f"🍷 {producer}, {wine} | {vintage}\n"
                f"🌍 {origin_level_1} - {region}\n"
                f"{price} kr\n"
                f"🔗 {product_url}\n\n"
                
            )

        return message

    except Exception as e:
        return f"Fel vid sökning: {e}"


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

    try:

        updates = bot.get_updates(
            offset=LAST_UPDATE_ID,
            timeout=10
        )

    except telegram.error.Conflict:

        print("⚠️ Annan bot-instans kör redan")
        return

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

                add_watch_sql(search_term)

                result = f"🍷 Tillagd i SQL-watchlist: {search_term}"
                
                bot.send_message(
                    chat_id=CHAT_ID,
                    text=result
                )

            #elif text.startswith("/remove "):
            #    
            #    search_term = text.replace("/remove ", "")
            #
            #      result = remove_watch(search_term)
            #
            #   bot.send_message(
            #       chat_id=CHAT_ID,
            #        text=result
            #    )

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

time.sleep(5)

#scan_systembolaget()
scan_local_products()

loaded_products = load_products_sql()

print(f"🍷 Loaded products: {len(loaded_products)}")

while True:
    schedule.run_pending()
    check_messages()
    time.sleep(5)
