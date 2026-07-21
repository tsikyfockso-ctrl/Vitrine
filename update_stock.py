import os
import requests
import json
import iop  # SDK officiel d'AliExpress / Taobao pour gérer la signature

# Récupération sécurisée des secrets GitHub
APP_KEY = os.environ.get("ALIEXPRESS_APP_KEY")
APP_SECRET = os.environ.get("ALIEXPRESS_APP_SECRET")

# Votre URL d'application web Google Apps Script
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbyOxZJjlRvmrw2U-al4CZa8ZsW4FsWwRkH9cMvRig84qqpwr0rp3lsnfpnjGjOAl8Xm/exec"

print("Connexion sécurisée à l'API officielle d'AliExpress via IOP Client...")

if not APP_KEY or not APP_SECRET:
    print("Erreur : Les clés secrètes AliExpress ne sont pas configurées dans GitHub !")
    exit(1)

try:
    # URL de passerelle officielle de l'API AliExpress (Open Platform)
    gateway_url = "https://api-sg.aliexpress.com/sync" # ou l'endpoint officiel selon votre zone
    
    # Initialisation du client officiel qui calcule automatiquement la signature conforme
    client = iop.IopClient(gateway_url, APP_KEY, APP_SECRET)

    # Création de la requête API officielle (Exemple pour récupérer les produits tendance/hot products)
    request = iop.IopRequest("aliexpress.affiliate.hotproduct.query")
    
    # Paramètres de la requête
    request.add_api_param("app_signature", "1")
    
    # Exécution de la requête avec signature intégrée
    response = client.execute(request)

    print("Réponse brute d'AliExpress :", response.body)

    # Analyse et envoi vers Google Sheets selon la structure de la réponse officielle
    # (Le SDK retourne un objet JSON contenant les résultats)
    data = json.loads(response.body)
    
    if "aliexpress_affiliate_hotproduct_query_response" in data:
        resultat_produits = data["aliexpress_affiliate_hotproduct_query_response"]["resp_result"]["result"]["products"]
        
        succes_count = 0
        for p in resultat_produits:
            produit_data = {
                "nom": p.get("product_title"),
                "prix": str(p.get("target_sale_price")),
                "img": p.get("product_main_image_url")
            }

            res = requests.post(WEB_APP_URL, json=produit_data)
            if res.status_code == 200:
                succes_count += 1

        print(f"Synchronisation réussie ! {succes_count} produits envoyés au Google Sheet.")
    else:
        print("Format de réponse inattendu ou restrictions sur l'API.")

except Exception as e:
    print(f"Erreur technique : {e}")
    exit(1)
