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

MAX_BUY_PRICE_EUR = 550.0  # Limite max du coût d'achat rendu FR
JPY_TO_EUR = 0.0062        # Taux JPY -> EUR

def get_real_product_image(product_url, title):
    """Scrape la fiche produit directe ZenMarket pour choper la vraie photo de l'annonce."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(product_url, headers=headers, timeout=8)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 1. Chercher l'image principale de la fiche ZenMarket / Mercari
            main_img = soup.find("img", id="item-photo") or soup.find("img", class_="item-img")
            if main_img and main_img.get("src"):
                return main_img["src"]

            # 2. Chercher la balise og:image si l'ID n'est pas trouvé
            og_image = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "og:image"})
            if og_image and og_image.get("content"):
                img_url = og_image["content"]
                if not any(bad in img_url.lower() for bad in ["logo", "banner", "icon", "default"]):
                    return img_url
    except Exception as e:
        print(f"⚠️ Erreur extraction image pour {product_url} : {e}")

    # Fallback si l'image ne peut pas être scrapée
    return "https://images.unsplash.com/photo-1584917865442-de89df76afd3?auto=format&fit=crop&w=600&q=80"

# EXEMPLES AVEC DES LIENS DIRECTS DE FICHES PRODUITS (remplace par tes vrais liens scrapés)
RAW_DEALS = [
    {
        "title": "Sac Louis Vuitton Speedy 25 Monogram",
        "buy_price_jpy": 38000,
        # Lien direct vers la FICHE PRODUIT d'un article spécifique sur ZenMarket (Mercari)
        "item_url": "https://zenmarket.jp/fr/auction.aspx?itemCode=m123456789" 
    },
    {
        "title": "Portefeuille Gucci GG Marmont Cuir Noir",
        "buy_price_jpy": 24000,
        "item_url": "https://zenmarket.jp/fr/auction.aspx?itemCode=m987654321"
    }
]

def run_bot():
    print("🚀 Anayse des fiches produits et extraction des photos d'annonces...")
    
    supabase.table("deals").delete().neq("title", "").execute()
    
    added_count = 0
    for item in RAW_DEALS:
        price_jpy = item["buy_price_jpy"]
        total_cost_eur = round(((price_jpy + 3500) * JPY_TO_EUR) * 1.20, 2)
        
        if total_cost_eur <= MAX_BUY_PRICE_EUR:
            estimated_resale_eur = round(total_cost_eur * 1.50, 2)
            estimated_profit = round((estimated_resale_eur * 0.85) - total_cost_eur, 2)
            
            # Récupère l'image réelle issue de la fiche produit
            image_url = get_real_product_image(item["item_url"], item["title"])

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
            print(f"✅ Fiche produit enregistrée : {item['title']}")

    print(f"✨ Bilan : {added_count} annonce(s) traitée(s).")

if __name__ == "__main__":
    run_bot()
