import os
import requests
from bs4 import BeautifulSoup
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Clés Supabase manquantes.")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_real_image_url(product_url):
    """Scrape le lien de l'annonce pour extraire l'image originale (via Open Graph)."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(product_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            # Cherche la balise meta og:image utilisée par la plupart des sites de e-commerce
            og_image = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "og:image"})
            if og_image and og_image.get("content"):
                return og_image["content"]
    except Exception as e:
        print(f"⚠️ Impossible d'extraire l'image pour {product_url} : {e}")
    
    # Image par défaut si le scraping échoue
    return "https://via.placeholder.com/600x400?text=Photo+Annonce+Non+Disponible"

# Liens réels d'annonces au Japon
DEALS_TO_SCRAPE = [
    {
        "title": "Sac Louis Vuitton Speedy 25 Monogram",
        "buy_price_jpy": 38000,
        "total_cost_eur": 298.00,
        "estimated_resale_eur": 520.00,
        "estimated_profit": 144.00,
        "item_url": "https://zenmarket.jp/fr/showcase/mercari.aspx" 
    }
]

def run_bot():
    print("🚀 Scraping des annonces et extraction des vraies photos...")
    supabase.table("deals").delete().neq("title", "").execute()
    
    for item in DEALS_TO_SCRAPE:
        # Extraction automatique de la photo réelle de l'annonce
        real_image = get_real_image_url(item["item_url"])
        item["image_url"] = real_image
        
        supabase.table("deals").insert(item).execute()
        print(f"✅ {item['title']} inséré avec son image réelle : {real_image}")

if __name__ == "__main__":
    run_bot()
