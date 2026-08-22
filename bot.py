import os
import requests
from supabase import create_client

# Connexion à Supabase via les clés sécurisées GitHub
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

JPY_TO_EUR = 0.0062  # À dynamiser si besoin

def run_bot():
    # Exemple de recherche sur flux public / API proxy
    url = "https://zenmarket.jp/api/search?q=Louis%20Vuitton&sort=created_desc"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        res = requests.get(url, headers=headers)
        items = res.json().get('items', [])
    except Exception:
        print("Erreur de connexion aux plateformes")
        return

    for item in items:
        price_jpy = item.get('price', 0)
        
        # Calcul : Prix d'achat + 3500 JPY (frais/port) + 20% TVA import
        cost_eur = ((price_jpy + 3500) * JPY_TO_EUR) * 1.20
        
        # Estimation revente FR (Modèle simplifié)
        est_resale = cost_eur * 1.6
        profit = (est_resale * 0.85) - cost_eur  # Déduction -15% Vinted/Vestiaire

        # Filtre pépites : Marge de plus de 50 €
        if profit > 50:
            # Insertion directe dans la base de données Supabase
            supabase.table("deals").insert({
                "title": item.get('title', 'Article Luxe'),
                "buy_price_jpy": price_jpy,
                "total_cost_eur": round(cost_eur, 2),
                "estimated_resale_eur": round(est_resale, 2),
                "estimated_profit": round(profit, 2),
                "item_url": item.get('url', '')
            }).execute()

if __name__ == "__main__":
    run_bot()
