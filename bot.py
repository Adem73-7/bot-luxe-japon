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
MAX_BUY_PRICE_EUR = 550.0  # Limite max du coût d'achat rendu FR
JPY_TO_EUR = 0.0062        # Taux de conversion approximatif JPY -> EUR

def get_real_item_image(product_url):
    """Extrait la vraie photo du sac depuis l'annonce en ignorant les logos."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    try:
        response = requests.get(product_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Recherche des balises images qui ne sont pas des logos/icônes
            images = soup.find_all("img")
            for img in images:
                src = img.get("src") or img.get("data-src")
                if src and "http" in src:
                    src_lower = src.lower()
                    if not any(bad in src_lower for bad in ["logo", "icon", "banner", "avatar", "svg", "static"]):
                        return src
            
            # Fallback sur meta og:image si valide
            og_image = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "og:image"})
            if og_image and og_image.get("content"):
                url = og_image["content"]
                if "logo" not in url.lower():
                    return url
    except Exception as e:
        print(f"⚠️ Erreur scraping image pour {product_url} : {e}")
    
    # Image par défaut si le scraping de l'annonce est bloqué
    return "https://images.unsplash.com/photo-1584917865442-de89df76afd3?auto=format&fit=crop&w=600&q=80"

# Flux d'annonces à analyser (à alimenter avec tes recherches d'articles au Japon)
RAW_DEALS = [
    {
        "title": "Sac Louis Vuitton Speedy 25 Monogram",
        "buy_price_jpy": 38000,
        "item_url": "https://zenmarket.jp/fr/showcase/mercari.aspx"
    },
    {
        "title": "Portefeuille Gucci GG Marmont Cuir Noir",
        "buy_price_jpy": 24000,
        "item_url": "https://doorzo.com"
    },
    {
        "title": "Sac Celine Luggage Nano (Hors Budget)",
        "buy_price_jpy": 120000,
        "item_url": "https://zenmarket.jp"
    }
]

def run_bot():
    print("🚀 Démarrage de la recherche (Plafond max : 550 €)...")
    
    added_count = 0
    for item in RAW_DEALS:
        price_jpy = item["buy_price_jpy"]
        
        # Calcul du coût total rendu en France : (Prix JPY + frais proxy 3500 JPY) * Taux * TVA 20%
        total_cost_eur = round(((price_jpy + 3500) * JPY_TO_EUR) * 1.20, 2)
        
        # FILTRE : Conserver uniquement les affaires sous le plafond de 550 €
        if total_cost_eur <= MAX_BUY_PRICE_EUR:
            
            # Vérification anti-doublon : le produit est-il déjà enregistré dans Supabase ?
            existing = supabase.table("deals").select("id").eq("title", item["title"]).execute()
            
            if not existing.data:
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
                print(f"✅ Nouvelle pépite enregistrée : {item['title']} ({total_cost_eur} €)")
            else:
                print(f"ℹ️ Déjà présent dans la base : {item['title']}")
        else:
            print(f"⛔ Ignoré (Prix supérieur à 550 €) : {item['title']} ({total_cost_eur} €)")

    print(f"✨ Bilan du passage : {added_count} nouvelle(s) pépite(s) ajoutée(s).")

if __name__ == "__main__":
    run_bot()
