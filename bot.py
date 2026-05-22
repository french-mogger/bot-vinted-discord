import time
import logging
import os
import requests
from vinted_scraper import VintedScraper

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
CHANNEL_ID = int(os.environ["CHANNEL_ID"])

SEARCHES = [
    {"search_text": "nike running", "price_to": 10},
    {"search_text": "Ralph Laurent torsadé", "price_to": 20},
]

seen_ids = set()
scraper = VintedScraper("https://www.vinted.fr")

def get_items(search):
    try:
        params = {
            "search_text": search["search_text"],
            "price_to": search["price_to"],
            "order": "newest_first",
            "per_page": 20,
        }
        items = scraper.search(params)
        logging.info(f"{len(items)} annonces pour '{search['search_text']}'")
        return items
    except Exception as e:
        logging.error(f"Erreur scraper: {e}")
        return []

def send_discord(item, search_text):
    # Extraire l'URL de la photo correctement
    photo_url = None
    if item.photo:
        if isinstance(item.photo, str):
            photo_url = item.photo
        elif isinstance(item.photo, dict):
            photo_url = item.photo.get("url")
        elif hasattr(item.photo, "url"):
            photo_url = item.photo.url

    embed = {
        "title": item.title,
        "url": item.url,
        "color": 0x09B1BA,
        "fields": [
            {"name": "🔍 Recherche", "value": search_text, "inline": True},
            {"name": "💶 Prix", "value": f"{item.price} {item.currency}", "inline": True},
            {"name": "📏 Taille", "value": item.size_title or "N/A", "inline": True},
        ],
    }

    if photo_url:
        embed["thumbnail"] = {"url": photo_url}

    r = requests.post(
        f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages",
        headers={
            "Authorization": f"Bot {DISCORD_TOKEN}",
            "Content-Type": "application/json"
        },
        json={"embeds": [embed]},
        timeout=10
    )
    logging.info(f"Discord status: {r.status_code}")

def run():
    logging.info("Bot démarré - chargement initial...")
    for search in SEARCHES:
        for item in get_items(search):
            seen_ids.add(item.id)
        time.sleep(3)
    logging.info(f"{len(seen_ids)} annonces ignorées au démarrage")

    while True:
        for search in SEARCHES:
            for item in get_items(search):
                if item.id not in seen_ids:
                    seen_ids.add(item.id)
                    send_discord(item, search["search_text"])
                    logging.info(f"🆕 {item.title} - {item.price}€")
                    time.sleep(1)
            time.sleep(5)
        time.sleep(60)

run()
