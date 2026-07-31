import os
import json
import requests

# Récupération de la clé API CJ depuis les secrets GitHub
CJ_API_KEY = os.environ.get("CJ_API_KEY")

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
    """Recherche des produits et de leurs variantes sur CJ Dropshipping."""
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

def generate_update_stock_json():
    print("🤖 Démarrage de la synchronisation CJ Dropshipping -> update_stock.json...")
    
    token = get_cj_access_token()
    if not token:
        print("❌ Arrêt du script : Impossible d'obtenir le jeton d'accès CJ.")
        return
    
    products_raw = fetch_cj_products_deep(token)
    print(f"📦 {len(products_raw)} produits principaux trouvés sur CJ.")
    
    formatted_products = []
    
    for product in products_raw:
        nom = product.get("productNameEn") or product.get("productName", "")
        variants = product.get("variants", [])
        
        tailles_values = [""] * 6
        prix_values = [""] * 6
        images_values = [""] * 7
        details_list = []
        total_stock = 0

        if variants:
            for idx, variant in enumerate(variants):
                v_size = str(variant.get("variantSize", "")).strip()
                v_price = str(variant.get("variantPrice", ""))
                v_image = variant.get("variantImage", "")
                v_stock = variant.get("variantStock", 0)
                v_key = variant.get("variantKey", "")
                
                try:
                    total_stock += int(v_stock)
                except ValueError:
                    pass

                pos = idx if idx < 6 else 5
                tailles_values[pos] = v_size
                prix_values[pos] = v_price
                if idx < 7:
                    images_values[idx] = v_image
                if v_key:
                    details_list.append(v_key)
        else:
            tailles_values[0] = str(product.get("productSize", ""))
            prix_values[0] = str(product.get("sellPrice", ""))
            images_values[0] = product.get("productImage", "")
            try:
                total_stock = int(product.get("sellStock", 0))
            except ValueError:
                total_stock = 0
            details_list.append(product.get("productSku", ""))

        product_obj = {
            "nom": nom,
            "tailles": tailles_values,
            "prix": prix_values,
            "images": images_values,
            "details": " | ".join(filter(None, details_list)),
            "stock": total_stock
        }
    
        formatted_products.append(product_obj)

    # Sauvegarde directe dans update_stock.json à la racine
    output_filename = "update_stock.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(formatted_products, f, ensure_ascii=False, indent=4)
        
    print(f"✨ Fichier {output_filename} généré avec succès !")

if __name__ == "__main__":
    generate_update_stock_json()
