import requests
import json
import os

# Récupération sécurisée de la clé API depuis les Secrets de GitHub Actions
CJ_API_KEY = os.environ.get("CJ_API_KEY")

def get_cj_access_token():
    """Récupère le token d'accès officiel auprès de l'API CJ via la clé API (apiKey mode)"""
    # Nouvel endpoint officiel pour l'authentification par API Key
    url = "https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken"
    
    if not CJ_API_KEY:
        print("❌ Erreur : La variable d'environnement CJ_API_KEY n'est pas définie dans les Secrets GitHub.")
        return None

    # Payload officiel avec la clé API
    payload = {
        "apiKey": CJ_API_KEY
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            if data.get("result"):
                return data.get("data", {}).get("accessToken")
            else:
                print(f"❌ Erreur API CJ (Token) : {data.get('message', 'Réponse invalide')}")
    except Exception as e:
        print(f"Erreur de connexion lors de la récupération du token : {e}")
    return None

def fetch_cj_products_deep(token):
    """Récupère les produits de vêtements pour femme depuis CJ et extrait proprement leur SKU"""
    url = "https://developers.cjdropshipping.com/api2.0/v1/product/list"
    headers = {
        "CJ-Access-Token": token,
        "Content-Type": "application/json"
    }
    
    # Paramètre de recherche ciblé sur les vêtements pour femme
    params = {
        "keyword": "women clothing",
        "pageSize": 20
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            products_list = data.get("data", {}).get("list", [])
            
            formatted_products = []
            for product in products_list:
                # Extraction sécurisée du SKU pour correspondance sur le site de CJ
                sku = product.get("productSku") or product.get("sku") or "N/A"
                
                # Construction de l'objet produit propre pour votre JSON
                formatted_product = {
                    "sku": sku,
                    "title": product.get("productName", "Produit sans titre"),
                    "price": product.get("sellPrice", 0.0),
                    "image": product.get("productImage", ""),
                    "description": product.get("description", "")
                }
                formatted_products.append(formatted_product)
                
            return formatted_products
            
    except Exception as e:
        print(f"Erreur de connexion lors de la récupération des produits CJ : {e}")
        
    return []

def generate_update_stock_json():
    print("🤖 Synchronisation, application des tarifs et traduction automatique en Français...")
    
    token = get_cj_access_token()
    if not token:
        print("❌ Erreur : Impossible d'obtenir le token d'accès CJ.")
        return

    products_raw = fetch_cj_products_deep(token)
    
    if products_raw:
        # Enregistrement dans le fichier JSON exploité par votre site web
        with open("update_stock.json", "w", encoding="utf-8") as f:
            json.dump(products_raw, f, ensure_ascii=False, indent=4)
            
        print(f"✅ Succès : {len(products_raw)} produits traduits, avec SKU, et synchronisés dans update_stock.json")
    else:
        print("⚠️ Aucun produit récupéré. Le fichier n'a pas pu être rempli.")

if __name__ == "__main__":
    generate_update_stock_json()
