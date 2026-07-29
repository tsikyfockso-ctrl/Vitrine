import os
import requests
import json
import time

# Récupération des secrets configurés (dans GitHub Actions ou en local)
CJ_API_KEY = os.getenv("CJ_API_KEY")
GOOGLE_SCRIPT_URL = os.getenv("GOOGLE_SCRIPT_URL")

# URLs officielles de l'API CJ Dropshipping V2
CJ_AUTH_URL = "https://developers.cjdropshipping.com/api2/v2/authentication/getToken"
CJ_SEARCH_URL = "https://developers.cjdropshipping.com/api2/v2/product/list"

def get_cj_token():
    """Génère ou récupère le jeton d'accès (Token) auprès de l'API CJ Dropshipping"""
    headers = {"Content-Type": "application/json"}
    payload = {"apiKey": CJ_API_KEY}
    
    try:
        response = requests.post(CJ_AUTH_URL, headers=headers, json=payload, timeout=15)
        data = response.json()
        if data.get("result"):
            token = data.get("data", {}).get("accessToken")
            print("🔑 Jeton d'accès CJ Dropshipping généré avec succès !")
            return token
        else:
            print(f"❌ Erreur d'authentification CJ : {data.get('message')}")
            return None
    except Exception as e:
        print(f"❌ Exception lors de la connexion à l'API CJ : {e}")
        return None

def fetch_cj_products(keyword="fashion accessories", limit=10):
    """Recherche des produits sur CJ Dropshipping et extrait leurs détails"""
    token = get_cj_token()
    if not token:
        return []

    headers = {
        "Content-Type": "application/json",
        "CJ-Access-Token": token
    }
    
    # Paramètres de recherche de l'API CJ
    params = {
        "keyWord": keyword,
        "page": 1,
        "size": limit
    }
    
    print(f"🌐 Recherche en cours sur CJ Dropshipping pour le mot-clé : '{keyword}'...")
    
    try:
        response = requests.post(CJ_SEARCH_URL, headers=headers, json=params, timeout=20)
        result = response.json()
        
        if result.get("result"):
            product_list = result.get("data", {}).get("productList", [])
            print(f"📦 {len(product_list)} produits trouvés sur CJ !")
            return product_list
        else:
            print(f"⚠️ Aucun produit récupéré : {result.get('message')}")
            return []
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des produits : {e}")
        return []

def send_to_google_sheet(product):
    """Envoie un produit formaté vers le Google Sheet via le script Apps Script"""
    if not GOOGLE_SCRIPT_URL:
        print("⚠️ URL Google Sheet non définie.")
        return

    # Adaptation des données aux colonnes de votre Google Sheet :
    # Col A: nom | Col B: prix | Col C: img | Col D: details | Col E: stock
    payload = {
        "nom": product.get("nameEn", "Nom indisponible")[:120],
        "prix": str(product.get("sellPrice", "0.00")),
        "img": product.get("bigImage", ""),
        "details": f"SPU: {product.get('spu', 'N/A')} - Fournisseur: {product.get('supplierName', 'CJ')}",
        "stock": str(product.get("warehouseInventoryNum", 0))
    }

    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(GOOGLE_SCRIPT_URL, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"   🚀 Envoyé avec succès au Google Sheet : {payload['nom'][:40]}...")
        else:
            print(f"   ⚠️ Erreur d'envoi Google Sheet (Code {response.status_code})")
    except Exception as e:
        print(f"   ❌ Exception lors de l'envoi vers Google Sheet : {e}")

if __name__ == "__main__":
    print("🤖 Démarrage du script de synchronisation CJ Dropshipping -> Google Sheet...")
    
    # Vous pouvez changer le mot-clé selon ce que vous souhaitez importer
    mots_cles = ["fashion accessories", "smartwatch"]
    
    for kw in mots_cles:
        products = fetch_cj_products(keyword=kw, limit=5)
        for prod in products:
            send_to_google_sheet(prod)
            time.sleep(1) # Pause brève entre chaque envoi pour stabiliser la requête
            
    print("✨ Synchronisation terminée avec succès !")
