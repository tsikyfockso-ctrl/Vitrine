import os
import requests

# Configuration des URLs de l'API CJ Dropshipping V2
BASE_URL = "https://developers.cjdropshipping.com/api2.0/v1"
TOKEN_URL = f"{BASE_URL}/authentication/getAccessToken"
SEARCH_URL = f"{BASE_URL}/product/queryProduct"

# Récupération de la clé API depuis les variables d'environnement (ou GitHub Secrets)
CJ_API_KEY = os.getenv("CJ_API_KEY")
GOOGLE_SCRIPT_URL = os.getenv("GOOGLE_SCRIPT_URL")

def get_access_token():
    print("🔑 Génération du jeton d'accès CJ Dropshipping...")
    headers = {"Content-Type": "application/json"}
    payload = {"apiKey": CJ_API_KEY}
    
    response = requests.post(TOKEN_URL, json=payload)
    print(f"📊 Code HTTP reçu pour le token : {response.status_code}")
    
    data = response.json()
    if data.get("result"):
        token = data.get("data", {}).get("accessToken")
        print("🔑 Jeton d'accès CJ Dropshipping généré avec succès !")
        return token
    else:
        print(f"❌ Erreur lors de la génération du token : {data}")
        return None

def search_products(token, keyword="fashion accessories"):
    print(f"🌐 Recherche en cours sur CJ Dropshipping pour : '{keyword}'...")
    
    headers = {
        "Content-Type": "application/json",
        "CJ-Access-Token": token
    }
    
    # Paramètres de recherche adaptés pour queryProduct (essayez productName ou keyword selon le retour)
    payload = {
        "productName": keyword,
        "pageNum": 1,
        "pageSize": 10
    }
    
    response = requests.post(SEARCH_URL, headers=headers, json=payload)
    print(f"📊 Code HTTP reçu pour la recherche : {response.status_code}")
    
    data = response.json()
    
    # Extraction sécurisée des produits selon la structure de l'API
    products = data.get("data", {}).get("list", [])
    print(f"📦 {len(products)} produits trouvés sur CJ !")
    
    return products

def send_to_google_sheet(products):
    if not products:
        print("⚠️ Aucun produit à envoyer vers Google Sheet.")
        return

    print("📤 Envoi des produits vers Google Sheet...")
    for product in products:
        # Adaptation des champs selon la structure renvoyée par CJ
        payload = {
            "nom": product.get("productName", "Nom indisponible"),
            "prix": product.get("sellPrice", "0"),
            "img": product.get("productImage", ""),
            "details": product.get("productSku", ""),
            "stock": product.get("totalStock", 0)
        }
        
        try:
            res = requests.post(GOOGLE_SCRIPT_URL, json=payload)
            if res.status_code == 200:
                print(f"✅ Produit ajouté : {payload['nom']}")
            else:
                print(f"⚠️ Erreur Google Sheet pour {payload['nom']} : {res.status_code}")
        except Exception as e:
            print(f"❌ Exception lors de l'envoi : {e}")

if __name__ == "__main__":
    print("🤖 Démarrage du script de synchronisation CJ Dropshipping -> Google Sheet...")
    token = get_access_token()
    if token:
        products = search_products(token, keyword="fashion accessories")
        send_to_google_sheet(products)
    print("✨ Synchronisation terminée avec succès !")
