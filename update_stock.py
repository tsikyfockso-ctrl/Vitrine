import requests
import json

# --- CONFIGURATION CJ DROPSHIPPING & GOOGLE SHEET ---
CJ_EMAIL = "tsikyfockso@gmail.com"
CJ_PASSWORD = "Adminserver12.."  # Ou clé API développeur CJ
GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SCRIPT_URL")
KEYWORD = "fashion accessories"

def get_cj_access_token():
    print("🔑 Génération du jeton d'accès CJ Dropshipping...")
    url = "https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken"
    payload = {
        "email": CJ_EMAIL,
        "password": CJ_PASSWORD
    }
    try:
        response = requests.post(url, json=payload)
        data = response.json()
        if data.get("result"):
            token = data["data"].get("accessToken")
            print("🔑 Jeton d'accès généré avec succès !")
            return token
        else:
            print(f"⚠️ Erreur d'authentification CJ : {data.get('message')}")
            return None
    except Exception as e:
        print(f"❌ Exception lors de la génération du token : {e}")
        return None

def sync_cj_to_googlesheet():
    print("🤖 Démarrage de la synchronisation CJ Dropshipping -> Google Sheet...")
    
    token = get_cj_access_token()
    if not token:
        print("❌ Arrêt du script : Jeton d'accès vide ou invalide.")
        return

    headers = {
        "CJ-Access-Token": token,
        "Content-Type": "application/json"
    }
    
    # Endpoint de recherche de produits CJ
    search_url = "https://developers.cjdropshipping.com/api2.0/v1/product/queryProduct"
    params = {
        "keyword": KEYWORD,
        "pageSize": 10
    }
    
    print(f"🌐 Recherche sur CJ Dropshipping pour : '{KEYWORD}'...")
    try:
        response = requests.post(search_url, headers=headers, json=params)
        result = response.json()
        
        if not result.get("result"):
            print(f"⚠️ Message API CJ : {result.get('message', 'Aucun produit')}")
            return
            
        products = result.get("data", {}).get("list", [])
        print(f"📦 {len(products)} produits trouvés sur CJ.")
        
        count_sent = 0
        for product in products:
            p_name = product.get("productName", "Produit sans nom")
            p_variants = product.get("variants", [])
            
            # Si le produit possède des variantes (tailles/couleurs)
            if p_variants:
                for variant in p_variants:
                    v_size = variant.get("variantSize", "Standard")
                    v_price = variant.get("variantPrice", "0.00")
                    v_img = variant.get("variantImage", product.get("productImage", ""))
                    v_sku = variant.get("variantSku", "")
                    v_stock = variant.get("inventory", 0)
                    
                    payload = {
                        "nom": p_name[:150],
                        "taille": v_size,
                        "prix": str(v_price),
                        "img": v_img,
                        "details": f"SKU: {v_sku}",
                        "stock": str(v_stock)
                    }
                    
                    # Envoi vers Google Sheet
                    res = requests.post(GOOGLE_SCRIPT_URL, json=payload)
                    if res.status_code == 200:
                        count_sent += 1
            else:
                # Produit simple sans variante
                payload = {
                    "nom": p_name[:150],
                    "taille": "Unique",
                    "prix": str(product.get("sellPrice", "0.00")),
                    "img": product.get("productImage", ""),
                    "details": f"SKU: {product.get('productSku', '')}",
                    "stock": str(product.get("inventory", 0))
                }
                res = requests.post(GOOGLE_SCRIPT_URL, json=payload)
                if res.status_code == 200:
                    count_sent += 1
                    
        print(f"✨ Synchronisation terminée avec succès ! {count_sent} lignes ajoutées/mises à jour dans Google Sheet.")
        
    except Exception as e:
        print(f"❌ Erreur durant la synchronisation : {e}")

if __name__ == "__main__":
    sync_cj_to_googlesheet()
