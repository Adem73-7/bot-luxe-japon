import os
import re
import requests
from bs4 import BeautifulSoup
from supabase import create_client

# Configuration Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Clés Supabase manquantes.")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# PARAMÈTRES
MAX_BUY_PRICE_EUR = 550.0  # Plafond max livré FR
JPY_TO_EUR = 0.0062        # Taux de conversion moyen JPY -> EUR

# User-Agent réaliste pour contourner les filtres basiques
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache"
})

SEARCH_QUERIES = [
    "Louis Vuitton Speedy",
    "Gucci GG Marmont",
    "Celine Luggage",
    "Chanel Vintage"
]

def get_official_product_image(title):
    """Fallback haute qualité : Récupère la photo officielle du modèle via Wikipédia/Wikimedia."""
    try:
        clean_title = " ".join(title.split()[:3])
        wiki_url = f"https://fr.wikipedia.org/w/api.php?action=query&titles={clean_title}&prop=pageimages&format=json&pithumbsize=600"
        res = SESSION.get(wiki_url, timeout=5).json()
        pages = res.get("query", {}).get("pages", {})
        for p_id in pages:
            if "thumbnail" in pages[p_id]:
                return pages[p_id]["thumbnail"]["source"]
    except Exception as e:
        print(f"⚠️ Erreur recherche image officielle pour {title} : {e}")
    
    return "https://images.unsplash.com/photo-1584917865442-de89df76afd3?auto=format&fit=crop&w=600&q=80"

def scrape_zenmarket_mercari(query):
    """Scrape les annonces réelles Mercari via ZenMarket avec gestion avancée des liens et images."""
    search_url = f"https://zenmarket.jp/fr/mercari.aspx?q={query.replace(' ', '+')}"
    found_items = []
    
    try:
        response = SESSION.get(search_url, timeout=12)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Recherche de tous les liens vers des fiches produits Mercari
            links = soup.find_all("a", href=re.compile(r"mercari\.aspx\?itemCode=|itemCode=m", re.I))
            
            seen_urls = set()
            for a_tag in links:
                href = a_tag.get("href", "")
                if not href:
                    continue
                
                # Construction d'une URL absolue valide vers la fiche produit exacte
                if href.startswith("http"):
                    item_url = href
                else:
                    item_url = f"https://zenmarket.jp{href}" if href.startswith("/") else f"https://zenmarket.jp/fr/{href}"
                
                if item_url in seen_urls:
                    continue
                seen_urls.add(item_url)
                
                # Extraction ou déduction du conteneur d'annonce
                parent = a_tag.find_parent("div") or a_tag
                
                # 1. Extraction de la photo
                img_tag = parent.find("img") or a_tag.find("img")
                image_url = ""
                if img_tag:
                    image_url = img_tag.get("src") or img_tag.get("data-src") or ""
                    if image_url and not image_url.startswith("http"):
                        image_url = f"https:{image_url}" if image_url.startswith("//") else f"https://zenmarket.jp{image_url}"
                
                # Si l'image est bloquée ou correspond à un logo/icône, passage au fallback officiel
                if not image_url or any(bad in image_url.lower() for bad in ["logo", "banner", "icon", "default", "static", "noimage"]):
                    image_url = get_official_product_image(query)

                # 2. Extraction du titre
                title_text = a_tag.get_text(strip=True) or parent.get_text(strip=True)
                title = title_text[:70] if len(title_text) > 5 else f"{query} - Occasion Japon"

                # 3. Extraction du prix en Yens
                price_text = parent.get_text()
                numbers = re.findall(r"¥\s*([\d,]+)|([\d,]+)\s*円", price_text)
                price_jpy = 0
                
                if numbers:
                    raw_num = [num for group in numbers[0] for num in group if num][0]
                    price_jpy = int(raw_num.replace(",", "").replace(" ", ""))
                else:
                    # Prix moyen estimé si non détecté directement dans la carte
                    price_jpy = 35000 

                found_items.append({
                    "title": title,
                    "buy_price_jpy": price_jpy,
                    "item_url": item_url,
                    "image_url": image_url
                })
    except Exception as e:
        print(f"⚠️ Erreur lors du scraping de '{query}' : {e}")

    return found_items

def run_bot():
    print("🚀 Auto-Bot Luxe Japon : Scan des annonces réelles...")
    added_count = 0

    for query in SEARCH_QUERIES:
        print(f"🔍 Recherche en cours pour : '{query}'...")
        items = scrape_zenmarket_mercari(query)
        
        for item in items:
            price_jpy = item["buy_price_jpy"]
            
            # Coût total livré FR (Prix JPY + 3 500 JPY frais proxy/port) * Taux EUR (SANS TVA)
            total_cost_eur = round((price_jpy + 3500) * JPY_TO_EUR, 2)
            
            # FILTRE STRICT : Seulement <= 550 €
            if total_cost_eur <= MAX_BUY_PRICE_EUR:
                # Anti-doublon par URL
                existing = supabase.table("deals").select("id").eq("item_url", item["item_url"]).execute()
                
                if not existing.data:
                    # Estimation revente (+50%)
                    estimated_resale_eur = round(total_cost_eur * 1.50, 2)
                    
                    # Profit Vinted (0% frais)
                    vinted_profit = round(estimated_resale_eur - total_cost_eur, 2)
                    
                    # Profit Vestiaire Collective (18% frais totaux)
                    vc_fees = estimated_resale_eur * 0.18
                    vc_profit = round(estimated_resale_eur - vc_fees - total_cost_eur, 2)

                    supabase.table("deals").insert({
                        "title": item["title"],
                        "buy_price_jpy": price_jpy,
                        "total_cost_eur": total_cost_eur,
                        "estimated_resale_eur": estimated_resale_eur,
                        "estimated_profit": vinted_profit,
                        "vinted_profit": vinted_profit,
                        "vc_profit": vc_profit,
                        "item_url": item["item_url"],
                        "image_url": item["image_url"]
                    }).execute()
                    
                    added_count += 1
                    print(f"✅ Pépite ajoutée : {item['title']} ({total_cost_eur} €) | Lien : {item['item_url']}")

    print(f"✨ Fin du scan : {added_count} nouvelle(s) annonce(s) enregistrée(s).")

if __name__ == "__main__":
    run_bot()
