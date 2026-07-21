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
    # Initialisation de l'API
    aliexpress = AliexpressApi(APP_KEY, APP_SECRET, models.Language.EN, models.Currency.EUR, "")

    # Liste complète de mots-clés couvrant toutes vos catégories
    mots_cles = [
        "women fashion",       # Mode femme
        "men fashion",         # Mode homme
        "kids clothing",       # Mode enfant
        "laptop accessories",  # Ordinateur
        "home accessories",    # Accessoire maison
        "home decor",          # Déco
        "beauty cosmetics",    # Produits cosmétiques
        "smartphone gadgets"   # Téléphone
    ]
    
    succes_total = 0

    # Boucle sur chaque catégorie / mot-clé
    for mot_cle in mots_cles:
        print(f"\nRecherche des produits pour la catégorie : '{mot_cle}'...")
        
        try:
            response = aliexpress.get_hotproducts(keywords=mot_cle, max_sale_price=100)
            produits_trouves = response.products
            print(f"{len(produits_trouves)} produits trouvés pour '{mot_cle}'.")

            for p in produits_trouves:
                produit_data = {
                    "nom": p.product_title,
                    "prix": str(p.target_sale_price),
                    "img": p.product_main_image_url
                }

                res = requests.post(WEB_APP_URL, json=produit_data)
                
                if res.status_code == 200:
                    succes_total += 1
                else:
                    print(f"Échec d'envoi pour : {p.product_title[:30]}")

        except Exception as err_mot_cle:
            print(f"Erreur pour la catégorie '{mot_cle}': {err_mot_cle}")

    print(f"\nSynchronisation terminée ! Au total, {succes_total} produits de toutes vos catégories ont été ajoutés à votre Google Sheet.")

except Exception as e:
    print(f"Erreur générale : {e}")
    exit(1)
