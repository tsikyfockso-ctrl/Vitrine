import os
import requests

# Récupération des secrets configurés dans GitHub Actions ou votre environnement
CJ_API_KEY = os.environ.get("CJ_API_KEY")
GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SCRIPT_URL")

def get_cj_access_token():
    """Génère le jeton d'accès valide pour l'API CJ via l'API Key."""
    url = "https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken"
    headers = {"Content-Type": "application/json"}
    payload = {"apiKey": CJ_API_KEY}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("result"):
                return data.get("data", {}).get("accessToken")
        print(f"⚠️ Erreur d'authentification CJ : {response.text}")
    except Exception as e:
        print(f"Erreur réseau lors de l'authentification : {e}")
    return None

def fetch_cj_products_deep(token):
    """Recherche des produits et de leurs variantes réelles sur CJ Dropshipping."""
    url = "https://developers.cjdropshipping.com/api2.0/v1/product/list"
    headers = {
        "CJ-Access-Token": token,
        "Content-Type": "application/json"
    }
    params = {"keyword": "fashion accessories"}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        print(f"📊 Code HTTP reçu de CJ : {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            return data.get("data", {}).get("list", [])
        else:
            print(f"Erreur API CJ : {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Erreur de connexion à l'API CJ : {e}")
        return []

def send_to_google_sheet(payload):
    """Envoie les données brutes extraites vers Google Apps Script."""
    try:
        response = requests.post(GOOGLE_SCRIPT_URL, json=payload)
        if response.status_code == 200:
            print(f"   🚀 Envoyé : {payload['nom']} | Taille: {payload['taille']} | Prix: {payload['prix_par_tailles']} | Stock: {payload['nombre_de_stock_disponible']}")
        else:
            print(f"   ⚠️ Erreur Google Sheet ({response.status_code}) - {response.text}")
    except Exception as e:
        print(f"   Erreur réseau Google Sheet : {e}")

def update_stock():
    print("🤖 Démarrage de la synchronisation CJ Dropshipping -> BDD_Mayah_Store...")
    
    token = get_cj_access_token()
    if not token:
        print("❌ Arrêt du script : Impossible d'obtenir le jeton d'accès CJ.")
        return
    
    products = fetch_cj_products_deep(token)
    print(f"📦 {len(products)} produits principaux trouvés sur CJ.")
    
    for product in products:
        # Récupération du nom en anglais (ou du nom brut si l'anglais n'est pas dispo)
        nom = product.get("productNameEn") or product.get("productName", "")
        variants = product.get("variants", [])
        
        # Si le produit possède de vraies variantes, on les extrait individuellement
        if variants:
            for variant in variants:
                payload = {
                    "nom": nom,
                    "taille": variant.get("variantSize", ""),
                    "prix_par_tailles": str(variant.get("variantPrice", "")),
                    "img_par_couleur": variant.get("variantImage", ""),
                    "details": variant.get("variantKey", ""),
                    "nombre_de_stock_disponible": str(variant.get("variantStock", ""))
                }
                send_to_google_sheet(payload)
        else:
            # Si le produit n'a pas de sous-variantes, on prend les données globales brutes
            payload = {
                "nom": nom,
                "taille": product.get("productSize", ""),
                "prix_par_tailles": str(product.get("sellPrice", "")),
                "img_par_couleur": product.get("productImage", ""),
                "details": product.get("productSku", ""),
                "nombre_de_stock_disponible": str(product.get("sellStock", ""))
            }
            send_to_google_sheet(payload)

    print("✨ Synchronisation terminée avec succès !")

if __name__ == "__main__":
    update_stock()
