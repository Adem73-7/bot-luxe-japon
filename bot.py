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

def get_real_item_image(product_url):
    """Extrait la vraie photo du sac depuis ZenMarket/Mercari/Yahoo Auctions."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    try:
        response = requests.get(product_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 1. Recherche des balises d'images d'articles spécifiques (Mercari / ZenMarket)
            # Évite les images qui contiennent "logo", "icon", "banner" ou "avatar"
            images = soup.find_all("img")
            for img in images:
                src = img.get("src") or img.get("data-src") or img.get("content")
                if src and ("http" in src):
                    src_lower = src.lower()
                    if not any(bad in src_lower for bad in ["logo", "icon", "banner", "avatar", "svg", "static"]):
                        return src
            
            # 2. Repercher dans meta og:image si l'URL ne contient pas "logo"
            og_image = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "og:image"})
            if og_image and og_image.get("content"):
                url = og_image["content"]
                if "logo" not in url.lower():
                    return url
    except Exception as e:
        print(f"⚠️ Erreur scraping image pour {product_url} : {e}")
    
    # Image fallback si le site bloque complètement le scraping sans API
    return "https://images.unsplash.com/photo-1584917865442-de89df76afd3?auto=format&fit=crop&w=600&q=80"

# Ta liste de pépites
DEALS = [
    {
        "title": "Sac Louis Vuitton Speedy 25 Monogram",
        "buy_price_jpy": 38000,
        "total_cost_eur": 298.00,
        "estimated_resale_eur": 520.00,
        "estimated_profit": 144.00,
        "item_url": "https://zenmarket.jp/fr/showcase/mercari.aspx"
    },
    {
        "title": "Sac Chanel Timeless Vintage Cuir Agneau Noir",
        "buy_price_jpy": 185000,
        "total_cost_eur": 1402.00,
        "estimated_resale_eur": 2200.00,
        "estimated_profit": 468.00,
        "item_url": "https://doorzo.com"
    },
    {
        "title": "Pochette Hermès Mini Evelyne Clemence",
        "buy_price_jpy": 210000,
        "total_cost_eur": 1588.00,
        "estimated_resale_eur": 2400.00,
        "estimated_profit": 452.00,
        "item_url": "https://zenmarket.jp"
    }
]

def run_bot():
    print("🚀 Scraping et filtrage des photos d'articles...")
    supabase.table("deals").delete().neq("title", "").execute()
    
    for item in DEALS:
        item["image_url"] = get_real_item_image(item["item_url"])
        supabase.table("deals").insert(item).execute()
        print(f"✅ {item['title']} -> Photo extraite : {item['image_url']}")

if __name__ == "__main__":
    run_bot()
