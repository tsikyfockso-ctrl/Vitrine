import os
import requests
from aliexpress_api import AliexpressApi, models

# Récupération sécurisée des secrets GitHub
APP_KEY = os.environ.get("ALIEXPRESS_APP_KEY")
APP_SECRET = os.environ.get("ALIEXPRESS_APP_SECRET")

# Votre URL d'application web Google Apps Script
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbyOxZJjlRvmrw2U-al4CZa8ZsW4FsWwRkH9cMvRig84qqpwr0rp3lsnfpnjGjOAl8Xm/exec"

print("Connexion à l'API officielle d'AliExpress...")

if not APP_KEY or not APP_SECRET:
    print("Erreur : Les clés secrètes AliExpress ne sont pas configurées dans GitHub !")
    exit(1)

try:
    # Initialisation de l'API AliExpress
    aliexpress = AliexpressApi(APP_KEY, APP_SECRET, models.Language.EN, models.Currency.EUR, "")

    print("Récupération des produits tendance globaux...")

    # Récupération d'une large sélection de produits tendance sans restreindre à un mot-clé unique
    response = aliexpress.get_hotproducts(max_sale_price=1000)
    
    produits_trouves = response.products
    print(f"{len(produits_trouves)} produits récupérés. Envoi vers Google Sheets...")

    succes_count = 0

    for p in produits_trouves:
        produit_data = {
            "nom": p.product_title,
            "prix": str(p.target_sale_price),
            "img": p.product_main_image_url
        }

        res = requests.post(WEB_APP_URL, json=produit_data)
        
        if res.status_code == 200:
            succes_count += 1
        else:
            print(f"Échec pour : {p.product_title[:30]}")

    print(f"Synchronisation réussie ! {succes_count} produits ajoutés à votre Google Sheet.")

except Exception as e:
    print(f"Erreur lors de la récupération : {e}")
    exit(1)
