import os
import requests

# Récupération des secrets configurés dans GitHub Actions
CJ_API_KEY = os.environ.get("CJ_API_KEY")
GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SHEET_URL")

def get_cj_access_token():
    """Génère ou récupère le jeton d'accès valide pour l'API CJ."""
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
    """Recherche approfondie des produits et de leurs variantes sur CJ Dropshipping."""
    url = "https://developers.cjdropshipping.com/api2.0/v1/product/list"
    headers = {
        "CJ-Access-Token": token,
        "Content-Type": "application/json"
    }
    # Vous pouvez élargir ou boucler sur plusieurs mots-clés si nécessaire
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
    """Envoie une ligne de variante détaillée vers Google Apps Script."""
    try:
        response = requests.post(GOOGLE_SCRIPT_URL, json=payload)
        if response.status_code == 200:
            print(f"   🚀 Envoyé : {payload['nom']} | Taille: {payload['taille']} | Prix: {payload['prix']} | Stock: {payload['stock']}")
        else:
            print(f"   ⚠️ Erreur Google Sheet ({response.status_code})")
    except Exception as e:
        print(f"   Erreur réseau Google Sheet : {e}")

def update_stock():
    print("🤖 Démarrage de la synchronisation approfondie CJ Dropshipping -> BDD_Mayah_Store...")
    
    token = get_cj_access_token()
    if not token:
        print("❌ Arrêt du script : Impossible d'obtenir le jeton d'accès CJ (Vérifiez votre CJ_API_KEY).")
        return
    
    products = fetch_cj_products_deep(token)
    print(f"📦 {len(products)} produits principaux trouvés sur CJ.")
    
    for product in products:
        nom = product.get("productName", "Nom indisponible")
        variants = product.get("variants", [])
        
        # Si le produit possède des variantes (tailles/couleurs multiples)
        if variants:
            for variant in variants:
                payload = {
                    "nom": nom,
                    "taille": variant.get("variantSize", "Standard"),
                    "prix": str(variant.get("variantPrice", product.get("sellPrice", "0"))),
                    "img": variant.get("variantImage", product.get("productImage", "")),
                    "details": variant.get("variantKey", product.get("productSku", "")),
                    "stock": str(variant.get("variantStock", 0))
                }
                send_to_google_sheet(payload)
        else:
            # Fallback si le produit n'a qu'une seule déclinaison globale
            payload = {
                "nom": nom,
                "taille": "Standard",
                "prix": str(product.get("sellPrice", "0")),
                "img": product.get("productImage", ""),
                "details": product.get("productSku", ""),
                "stock": str(product.get("sellStock", 0))
            }
            send_to_google_sheet(payload)

    print("✨ Synchronisation approfondie terminée avec succès !")

if __name__ == "__main__":
    update_stock()
