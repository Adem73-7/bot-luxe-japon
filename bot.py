import os
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Clés Supabase manquantes.")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Liste de pépites avec images
DEALS = [
    {
        "title": "Sac Louis Vuitton Speedy 25 Monogram",
        "buy_price_jpy": 38000,
        "total_cost_eur": 298.00,
        "estimated_resale_eur": 520.00,
        "estimated_profit": 144.00,
        "item_url": "https://zenmarket.jp",
        "image_url": "https://images.unsplash.com/photo-1584917865442-de89df76afd3?auto=format&fit=crop&w=600&q=80"
    },
    {
        "title": "Sac Chanel Timeless Vintage Cuir Agneau Noir",
        "buy_price_jpy": 185000,
        "total_cost_eur": 1402.00,
        "estimated_resale_eur": 2200.00,
        "estimated_profit": 468.00,
        "item_url": "https://doorzo.com",
        "image_url": "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?auto=format&fit=crop&w=600&q=80"
    },
    {
        "title": "Pochette Hermès Mini Evelyne Clemence",
        "buy_price_jpy": 210000,
        "total_cost_eur": 1588.00,
        "estimated_resale_eur": 2400.00,
        "estimated_profit": 452.00,
        "item_url": "https://zenmarket.jp",
        "image_url": "https://images.unsplash.com/photo-1590874103328-eac38a683ce7?auto=format&fit=crop&w=600&q=80"
    }
]

def run_bot():
    print("🚀 Nettoyage et envoi des nouvelles pépites...")
    # On vide les anciennes données sans image
    supabase.table("deals").delete().neq("title", "").execute()
    
    for item in DEALS:
        supabase.table("deals").insert(item).execute()
    print("✅ Pépites avec photos enregistrées !")

if __name__ == "__main__":
    run_bot()
