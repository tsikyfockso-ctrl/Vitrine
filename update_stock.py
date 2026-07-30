import requests
import json

# --- CONFIGURATION ---
# Remplacez par votre clé API développeur CJ Dropshipping (Mode apiKey exigé)
CJ_API_KEY = "CJ5666729@api@480a575a9fba476fb43e088979687236" 

# Remplacez par l'URL de votre application web Google Apps Script récupérée à l'étape 1
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyOxZJjlRvmrw2U-al4CZa8ZsW4FsWwRkH9cMvRig84qqpwr0rp3lsnfpnjGjOAl8Xm/exec"

# Mot-clé de recherche de produits sur CJ
SEARCH_KEYWORD = "fashion accessories"

def get_cj_access_token():
    """Génération du jeton d'accès CJ Dropshipping en mode apiKey"""
    url = "https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken"
    headers = {"Content-Type": "application/json"}
    payload = {"apiKey": CJ_API_KEY}
    
    print("🔑 Génération du jeton d'accès CJ Dropshipping (Mode API Key)...")
    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        
        if data.get("result") and data.get("data"):
            token = data["data"].get("accessToken")
            if token:
                print("🔑 Jeton d'accès généré avec succès !")
                return token
        
        print(f"⚠️ Erreur d'authentification CJ : {data.get('message', 'Erreur inconnue')}")
    except Exception as e:
        print(f"❌ Erreur de connexion lors de l'authentification : {e}")
        
    return None

def sync_cj_to_sheet():
    print("🤖 Démarrage de la synchronisation CJ Dropshipping -> Google Sheet...")
    
    token = get_cj_access_token()
    if not token:
        print("❌ Arrêt du script : Jeton d'accès vide ou invalide.")
        return

    # Recherche des produits sur l'API CJ
    search_url = "https://developers.cjdropshipping.com/api2.0/v1/product/list"
    headers = {
        "Content-Type": "application/json",
        "CJ-Access-Token": token
    }
    params = {
        "productName": SEARCH_KEYWORD,
        "size": 10 # Nombre de produits à récupérer
    }
    
    print(f"🌐 Recherche sur CJ Dropshipping pour : '{SEARCH_KEYWORD}'...")
    try:
        response = requests.get(search_url, headers=headers, params=params)
        result = response.json()
        
        print(f"📊 Code HTTP reçu de CJ : {response.status_code}")
        
        products = []
        if result.get("result") and result.get("data"):
            # Gère selon la structure de pagination de l'API CJ
            products = result["data"].get("list", [])
            if not products and isinstance(result["data"], list):
                products = result["data"]
                
        print(f"📦 {len(products)} produits trouvés sur CJ.")
        
        for prod in products:
            title = prod.get("productName", "Produit sans nom")
            # Extraction des informations de variantes, prix et stock si disponibles
            variants = prod.get("variants", [{}])
            
            for variant in variants:
                size = variant.get("variantSize", "Standard")
                price = str(variant.get("variantPrice", "0"))
                img_url = variant.get("variantImage") or prod.get("productImage", "")
                stock_qty = str(variant.get("variantStock", "0"))
                details = f"SKU: {variant.get('variantSku', 'N/A')} | Poids: {variant.get('variantWeight', 'N/A')}g"
                
                # Payload respectant l'ordre de votre Google Sheet BDD_Mayah_Store
                payload = {
                    "nom": title[:120],
                    "taille": size,
                    "prix": price,
                    "img": img_url,
                    "details": details,
                    "stock": stock_qty
                }
                
                # Envoi vers Google Sheet
                res = requests.post(GOOGLE_SCRIPT_URL, json=payload)
                if res.status_code == 200:
                    print(f"🚀 Envoyé au Google Sheet : {title[:30]}... (Taille: {size})")
                else:
                    print(f"⚠️ Erreur d'envoi Google Sheet pour {title[:30]}")
                    
        print("✨ Synchronisation terminée avec succès !")
        
    except Exception as e:
        print(f"❌ Erreur durant la synchronisation : {e}")

if __name__ == "__main__":
    sync_cj_to_sheet()
