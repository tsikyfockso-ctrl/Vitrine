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
    # Initialisation de l'API (Langue Anglais pour de meilleurs résultats, Devise EUR)
    aliexpress = AliexpressApi(APP_KEY, APP_SECRET, models.Language.EN, models.Currency.EUR, "")

    # Liste de vos catégories traduites en mots-clés optimisés pour l'API
    categories_mots_cles = {
        "Mode Femme": "women fashion clothing",
        "Mode Homme": "men fashion clothing",
        "Mode Enfant": "kids clothing baby",
        "Ordinateur": "laptop accessories computer",
        "Accessoire Maison": "home gadget kitchen tool",
        "Déco": "home decoration interior",
        "Produit Cosmétique": "beauty makeup skincare"
    }
    
    succes_total = 0

    # Boucle sur chaque catégorie
    for categorie, mot_cle in categories_mots_cles.items():
        print(f"\n--- Récupération pour la catégorie : {categorie} ('{mot_cle}') ---")
        
        try:
            response = aliexpress.get_hotproducts(keywords=mot_cle, max_sale_price=100)
            produits_trouves = response.products
            print(f"{len(produits_trouves)} produits trouvés pour {categorie}.")

            for p in produits_trouves:
                produit_data = {
                    "nom": f"[{categorie}] {p.product_title}",
                    "prix": str(p.target_sale_price),
                    "img": p.product_main_image_url
                }

                res = requests.post(WEB_APP_URL, json=produit_data)
                
                if res.status_code == 200:
                    succes_total += 1
                else:
                    print(f"Échec d'envoi pour : {p.product_title[:30]}")

        except Exception as err_cat:
            print(f"Erreur pour la catégorie '{categorie}': {err_cat}")

    print(f"\nSynchronisation globale terminée ! Au total, {succes_total} produits ont été ajoutés à votre Google Sheet.")

except Exception as e:
    print(f"Erreur générale : {e}")
    exit(1)
