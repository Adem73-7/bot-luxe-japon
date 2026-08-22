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

# PARAMÈTRES DU BOT
MAX_BUY_PRICE_EUR = 550.0  # Limite maximale du prix d'achat livré FR
JPY_TO_EUR = 0.0062        # Taux de conversion approximatif JPY -> EUR

def get_real_item_image(product_url):
    """Extrait la photo réelle de l'annonce en évitant les logos."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(product_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            images = soup.find_all("img")
            for img in images:
                src = img.get("src") or img.get("data-src")
                if src and "http" in src:
                    src_lower = src.lower()
                    if not any(bad in src_lower for bad in ["logo", "icon", "banner", "avatar", "svg"]):
                        return src
            og_image = soup.find("meta", property="og:image")
            if og_image and og_image.get("content"):
                return og_image["content"]
    except Exception as e:
        print(f"⚠️ Erreur extraction image : {e}")
    
    return "https://images.unsplash.com/photo-1584917865442-de89df76afd3?auto=format&fit=crop&w=600&q=80"

# Liste des annonces analysées par le bot
RAW_DEALS = [
    {
        "title": "Sac Louis Vuitton Speedy 25 Monogram",
        "buy_price_jpy": 38000,
        "item_url": "https://zenmarket.jp/fr/showcase/mercari.aspx"
    },
    {
        "title": "Portefeuille Gucci GG Marmont Cuir",
        "buy_price_jpy": 24000,
        "item_url": "https://doorzo.com"
    },
    {
        "title": "Sac Celine Luggage (Hors Budget)",
        "buy_price_jpy": 120000,
        "item_url": "https://zenmarket.jp"
    }
]

def run_bot():
    print("🚀 Démarrage de la recherche (Plafond max : 550 €)...")
    
    # Nettoie la table avant la mise à jour
    supabase.table("deals").delete().neq("title", "").execute()

    added_count = 0
    for item in RAW_DEALS:
        price_jpy = item["buy_price_jpy"]
        
        # Calcul du coût total rendu en France (Prix JPY + frais proxy) * taux * TVA 20%
        total_cost_eur = round(((price_jpy + 3500) * JPY_TO_EUR) * 1.20, 2)
        
        # FILTRE : On conserve uniquement si le coût total est <= 550 €
        if total_cost_eur <= MAX_BUY_PRICE_EUR:
            estimated_resale_eur = round(total_cost_eur * 1.50, 2)
            estimated_profit = round((estimated_resale_eur * 0.85) - total_cost_eur, 2)
            image_url = get_real_item_image(item["item_url"])

            supabase.table("deals").insert({
                "title": item["title"],
                "buy_price_jpy": price_jpy,
                "total_cost_eur": total_cost_eur,
                "estimated_resale_eur": estimated_resale_eur,
                "estimated_profit": estimated_profit,
                "item_url": item["item_url"],
                "image_url": image_url
            }).execute()
            
            added_count += 1
            print(f"✅ Ajouté : {item['title']} ({total_cost_eur} €)")
        else:
            print(f"⛔ Ignoré (Hors budget) : {item['title']} ({total_cost_eur} €)")

    print(f"✨ Bilan : {added_count} pépite(s) sous les 550 € enregistrée(s).")

if __name__ == "__main__":
    run_bot()
