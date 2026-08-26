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

# PARAMÈTRES DE RECHERCHE & FILTRES
MAX_BUY_PRICE_EUR = 550.0  # Plafond maximum livré FR
JPY_TO_EUR = 0.0062        # Taux de conversion moyen JPY -> EUR
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7"
}

# Mots-clés de sacs de luxe à surveiller au Japon
SEARCH_QUERIES = [
    "Louis Vuitton Speedy",
    "Gucci GG Marmont",
    "Celine Luggage",
    "Chanel Vintage"
]

def scrape_zenmarket_mercari(query):
    """Scrape le flux d'annonces récentes sur ZenMarket Mercari pour un mot-clé."""
    search_url = f"https://zenmarket.jp/fr/mercari.aspx?q={query.replace(' ', '+')}"
    found_items = []
    
    try:
        response = requests.get(search_url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Repérage des cartes d'articles dans les résultats
            product_cards = soup.find_all("div", class_=re.compile(r"item-card|product-item|mercari-item", re.I))
            
            for card in product_cards:
                # 1. Lien direct vers la fiche produit
                link_tag = card.find("a", href=True)
                if not link_tag:
                    continue
                href = link_tag["href"]
                item_url = href if href.startswith("http") else f"https://zenmarket.jp{href}"
                
                # 2. Vraie photo de l'article
                img_tag = card.find("img")
                image_url = ""
                if img_tag:
                    image_url = img_tag.get("src") or img_tag.get("data-src") or ""
                    if image_url and not image_url.startswith("http"):
                        image_url = f"https:{image_url}" if image_url.startswith("//") else f"https://zenmarket.jp{image_url}"
                
                # Éviter les logos ou images par défaut
                if any(bad in image_url.lower() for bad in ["logo", "banner", "icon", "default", "static"]):
                    image_url = "https://images.unsplash.com/photo-1584917865442-de89df76afd3?auto=format&fit=crop&w=600&q=80"

                # 3. Titre du produit
                title_tag = card.find(class_=re.compile(r"title|name", re.I)) or link_tag
                title = title_tag.get_text(strip=True) if title_tag else query

                # 4. Extraction du prix JPY
                price_tag = card.find(text=re.compile(r"¥|JPY|\d+"))
                price_jpy = 0
                if price_tag:
                    numbers = re.findall(r"\d+", price_tag.replace(",", "").replace(" ", ""))
                    if numbers:
                        price_jpy = int(numbers[0])

                if price_jpy > 0 and item_url:
                    found_items.append({
                        "title": title[:80],
                        "buy_price_jpy": price_jpy,
                        "item_url": item_url,
                        "image_url": image_url
                    })
    except Exception as e:
        print(f"⚠️ Erreur lors du scraping de {query} : {e}")

    return found_items

def run_bot():
    print("🚀 Auto-Bot : Analyse Vinted VS Vestiaire Collective...")
    added_count = 0

    for query in SEARCH_QUERIES:
        print(f"🔍 Analyse pour : '{query}'...")
        items = scrape_zenmarket_mercari(query)
        
        for item in items:
            price_jpy = item["buy_price_jpy"]
            
            # Coût total (Prix JPY + 3500 JPY frais/port) * Taux EUR (SANS TVA)
            total_cost_eur = round((price_jpy + 3500) * JPY_TO_EUR, 2)
            
            # FILTRE STRICT : Uniquement <= 550 €
            if total_cost_eur <= MAX_BUY_PRICE_EUR:
                # Anti-doublon par URL d'annonce
                existing = supabase.table("deals").select("id").eq("item_url", item["item_url"]).execute()
                
                if not existing.data:
                    # Cote de marché estimée en France (+50% par rapport au prix d'achat)
                    estimated_resale_eur = round(total_cost_eur * 1.50, 2)
                    
                    # 1. Bénéfice Vinted (0% frais vendeur)
                    vinted_profit = round(estimated_resale_eur - total_cost_eur, 2)
                    
                    # 2. Bénéfice Vestiaire Collective (15% commission + 3% frais paiement = 18% frais totaux)
                    vc_fees = estimated_resale_eur * 0.18
                    vc_profit = round(estimated_resale_eur - vc_fees - total_cost_eur, 2)

                    supabase.table("deals").insert({
                        "title": item["title"],
                        "buy_price_jpy": price_jpy,
                        "total_cost_eur": total_cost_eur,
                        "estimated_resale_eur": estimated_resale_eur,
                        "estimated_profit": vinted_profit, # Champ standard pour compatibilité
                        "vinted_profit": vinted_profit,
                        "vc_profit": vc_profit,
                        "item_url": item["item_url"],
                        "image_url": item["image_url"]
                    }).execute()
                    
                    added_count += 1
                    print(f"✅ NOUVELLE PÉPITE : {item['title']} ({total_cost_eur} €) | Profit Vinted: +{vinted_profit}€ | Profit VC: +{vc_profit}€")

    print(f"✨ Bilan du scan : {added_count} nouvelle(s) annonce(s) ajoutée(s).")

if __name__ == "__main__":
    run_bot()
