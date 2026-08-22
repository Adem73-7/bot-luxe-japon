import os
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Clés Supabase manquantes.")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Liste de pépites de luxe dénichées au Japon
DEALS = [
    {
        "title": "Sac Louis Vuitton Speedy 25 Monogram",
        "buy_price_jpy": 38000,
        "total_cost_eur": 298.00,
        "estimated_resale_eur": 520.00,
        "estimated_profit": 144.00,
        "item_url": "https://zenmarket.jp"
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
    print("🚀 Envoi des pépites vers Supabase...")
    for item in DEALS:
        supabase.table("deals").insert(item).execute()
    print("✅ Pépites enregistrées avec succès !")

if __name__ == "__main__":
    run_bot()
