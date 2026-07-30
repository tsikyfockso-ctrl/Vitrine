import os
import requests

# Récupération des clés depuis l'environnement
CJ_API_KEY = os.getenv("CJ_API_KEY")
GOOGLE_SCRIPT_URL = os.getenv("GOOGLE_SCRIPT_URL")

def get_access_token():
    print("🔑 Génération du jeton d'accès CJ Dropshipping...")
    url = "https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken"
    headers = {"Content-Type": "application/json"}
    payload = {"apiKey": CJ_API_KEY}
    
    response = requests.post(url, json=payload, headers=headers)
    try:
        data = response.json()
        if data.get("success"):
            print("🔑 Jeton d'accès généré avec succès !")
            return data.get("data", {}).get("accessToken")
        else:
            print(f"❌ Erreur token : {data.get('message')}")
            return None
    except Exception as e:
        print(f"❌ Exception token : {e}")
        return None

def search_products(token, keyword="fashion accessories"):
    print(f"🌐 Recherche sur CJ Dropshipping pour : '{keyword}'...")
    url = "https://developers.cjdropshipping.com/api2.0/v1/product/queryProduct"
    headers = {
        "Content-Type": "application/json",
        "Access-Token": token
    }
    payload = {"productName": keyword}
    
    response = requests.post(url, json=payload, headers=headers)
    try:
        data = response.json()
        if data.get("success"):
            return data.get("data", {}).get("list", [])
        else:
            print(f"⚠️ Message API CJ : {data.get('message')}")
            return []
    except Exception as e:
        print(f"❌ Erreur recherche produits : {e}")
        return []

def send_to_google_sheet(product):
    nom = product.get("productName", "Nom inconnu")
    details = product.get("productDetail", "Pas de détails")
    variants = product.get("variants", [])
    
    if variants:
        for variant in variants:
            taille = variant.get("variantName", "Standard")
            prix = variant.get("sellPrice", product.get("sellPrice", "0"))
            img = variant.get("variantImage", product.get("productImage", ""))
            stock = variant.get("inventory", product.get("totalStock", "0"))
            
            payload = {
                "nom": nom,
                "taille": taille,
                "prix": str(prix),
                "img": img,
                "details": details,
                "stock": str(stock)
            }
            
            response = requests.post(GOOGLE_SCRIPT_URL, json=payload)
            if response.status_code == 200:
                print(f"✅ Variante '{taille}' envoyée pour : {nom}")
            else:
                print(f"⚠️ Erreur d'envoi Google Sheet pour {nom}")
    else:
        # Produit simple sans variante multiple
        payload = {
            "nom": nom,
            "taille": "Unique",
            "prix": str(product.get("sellPrice", "0")),
            "img": product.get("productImage", ""),
            "details": details,
            "stock": str(product.get("totalStock", "0"))
        }
        response = requests.post(GOOGLE_SCRIPT_URL, json=payload)
        if response.status_code == 200:
            print(f"✅ Produit envoyé : {nom}")

if __name__ == "__main__":
    print("🤖 Démarrage de la synchronisation CJ Dropshipping -> Google Sheet...")
    token = get_access_token()
    if token:
        products = search_products(token, keyword="fashion accessories")
        print(f"📦 {len(products)} produits trouvés sur CJ.")
        for product in products:
            send_to_google_sheet(product)
            
    print("✨ Synchronisation terminée avec succès !")
