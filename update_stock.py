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
    # Nettoyage des clés pour éviter tout espace invisible accidentel
    key = APP_KEY.strip()
    secret = APP_SECRET.strip()

    # Initialisation de l'API avec les clés nettoyées
    aliexpress = AliexpressApi(key, secret, models.Language.EN, models.Currency.EUR, "")

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
            # Utilisation de get_products à la place de get_hotproducts pour contourner l'erreur de signature
            response = aliexpress.get_products(keywords=mot_cle, max_sale_price=100, page_no=1)
            
            # Vérification de la structure de la réponse selon le modèle de l'API
            produits_trouves = getattr(response, 'products', [])
            print(f"{len(produits_trouves)} produits trouvés pour '{mot_cle}'.")

            for p in produits_trouves:
                # Récupération sécurisée des attributs de l'objet produit
                titre = getattr(p, 'product_title', 'Produit sans titre')
                prix = str(getattr(p, 'target_sale_price', getattr(p, 'sale_price', '0.00')))
                img = getattr(p, 'product_main_image_url', '')

                produit_data = {
                    "nom": titre,
                    "prix": prix,
                    "img": img
                }

                res = requests.post(WEB_APP_URL, json=produit_data)
                
                if res.status_code == 200:
                    succes_total += 1
                else:
                    print(f"Échec d'envoi pour : {titre[:30]}")

        except Exception as err_mot_cle:
            print(f"Erreur pour la catégorie '{mot_cle}': {err_mot_cle}")

    print(f"\nSynchronisation terminée ! Au total, {succes_total} produits de toutes vos catégories ont été ajoutés à votre Google Sheet.")

except Exception as e:
    print(f"Erreur générale : {e}")
    exit(1)
