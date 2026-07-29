import os
import requests
import json
import time

# Récupération des secrets
CJ_API_KEY = os.getenv("CJ_API_KEY")
GOOGLE_SCRIPT_URL = os.getenv("GOOGLE_SCRIPT_URL")

# URLs officielles basées sur votre documentation (api2.0/v1)
CJ_AUTH_URL = "https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken"
CJ_SEARCH_URL = "https://developers.cjdropshipping.com/api2.0/v1/product/list"

def get_cj_token():
    """Génère ou récupère le jeton d'accès auprès de l'API CJ Dropshipping"""
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    payload = {"apiKey": CJ_API_KEY}
    
    try:
        response = requests.post(CJ_AUTH_URL, headers=headers, json=payload, timeout=15)
        print(f"📊 Code HTTP reçu de CJ : {response.status_code}")
        
        if not response.text or not response.text.strip():
            print("❌ Erreur : L'API CJ a renvoyé une réponse vide.")
            return None
            
        try:
            data = response.json()
        except json.JSONDecodeError:
            print(f"❌ Erreur : La réponse n'est pas du JSON. Texte brut reçu : {response.text[:300]}")
            return None

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

def fetch_cj_products(keyword="fashion accessories", limit=3):
    """Recherche des produits sur CJ Dropshipping via GET"""
    token = get_cj_token()
    if not token:
        return []

    headers = {
        "Content-Type": "application/json",
        "CJ-Access-Token": token,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    # Paramètres passés en GET (query params)
    params = {
        "keyWord": keyword,
        "page": 1,
        "size": limit
    }
    
    print(f"🌐 Recherche en cours sur CJ Dropshipping pour : '{keyword}'...")
    
    try:
        # Modification ici : utilisation de requests.get au lieu de requests.post
        response = requests.get(CJ_SEARCH_URL, headers=headers, params=params, timeout=20)
        
        if not response.text or not response.text.strip():
            print("⚠️ Réponse de recherche vide.")
            return []
            
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
    """Envoie un produit formaté vers le Google Sheet"""
    if not GOOGLE_SCRIPT_URL:
        print("⚠️ URL Google Sheet non définie.")
        return

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
    
    mots_cles = ["fashion accessories"]
    
    for kw in mots_cles:
        products = fetch_cj_products(keyword=kw, limit=3)
        for prod in products:
            send_to_google_sheet(prod)
            time.sleep(1)
            
    print("✨ Synchronisation terminée avec succès !")
