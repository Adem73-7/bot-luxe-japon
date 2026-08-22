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
JPY_TO_EUR = 0.0062        # Taux de conversion approximatif JPY -> EUR

def get_brand_representation_image(title):
    """Recherche une image représentative officielle via l'API Wikipedia si le scraping échoue."""
    try:
        # Nettoyage du titre pour chercher les mots-clés (ex: "Louis Vuitton Speedy 25")
        keywords = " ".join(title.split()[:4])
        wiki_url = f"https://fr.wikipedia.org/w/api.php?action=query&titles={keywords}&prop=pageimages&format=json&pithumbsize=600"
        res = requests.get(wiki_url, timeout=5).json()
        pages = res.get("query", {}).get("pages", {})
        for p_id in pages:
            if "thumbnail" in pages[p_id]:
                return pages[p_id]["thumbnail"]["source"]
    except Exception as e:
        print(f"⚠️ Erreur recherche image Wikipédia pour {title} : {e}")
    
    # Image fallback haute qualité pour le luxe si aucune image trouvée
    return "https://images.unsplash.com/photo-1584917865442-de89df76afd3?auto=format&fit=crop&w=600&q=80"

def get_item_image(product_url, title):
    """Tente d'extraire la photo originale, sinon bascule sur une image réelle du modèle."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(product_url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Balise meta og:image standard
            og_image = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "og:image"})
            if og_image and og_image.get("content"):
                img_url = og_image["content"]
                # S'assurer que ce n'est pas le logo du site
                if not any(bad in img_url.lower() for bad in ["logo", "banner", "icon", "zenmarket", "default"]):
                    return img_url
    except Exception as e:
        print(f"⚠️ Erreur scraping direct pour {product_url} : {e}")

    # Si le site proxy bloque l'image, on cherche une photo représentative du modèle
    return get_brand_representation_image(title)

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
    print("🚀 Démarrage du bot avec recherche d'images représentatives...")
    
    added_count = 0
    for item in RAW_DEALS:
        price_jpy = item["buy_price_jpy"]
        total_cost_eur = round(((price_jpy + 3500) * JPY_TO_EUR) * 1.20, 2)
        
        if total_cost_eur <= MAX_BUY_PRICE_EUR:
            existing = supabase.table("deals").select("id").eq("title", item["title"]).execute()
            
            if not existing.data:
                estimated_resale_eur = round(total_cost_eur * 1.50, 2)
                estimated_profit = round((estimated_resale_eur * 0.85) - total_cost_eur, 2)
                
                # Récupère soit la vraie photo de l'annonce soit l'image du produit
                image_url = get_item_image(item["item_url"], item["title"])

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
                print(f"✅ Ajouté : {item['title']} avec image : {image_url}")
            else:
                print(f"ℹ️ Déjà présent : {item['title']}")
        else:
            print(f"⛔ Ignoré (> 550 €) : {item['title']}")

    print(f"✨ Bilan : {added_count} pépite(s) traitée(s).")

if __name__ == "__main__":
    run_bot()
