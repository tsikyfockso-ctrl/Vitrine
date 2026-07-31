import os
import json
import requests

CJ_API_KEY = os.environ.get("CJ_API_KEY")

def get_cj_access_token():
    url = "https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken"
    headers = {"Content-Type": "application/json"}
    payload = {"apiKey": CJ_API_KEY}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("result"):
                return data.get("data", {}).get("accessToken")
    except Exception as e:
        print(f"Erreur d'authentification CJ : {e}")
    return None

def fetch_cj_products_deep(token):
    url = "https://developers.cjdropshipping.com/api2.0/v1/product/list"
    headers = {
        "CJ-Access-Token": token,
        "Content-Type": "application/json"
    }
    params = {"keyword": "fashion accessories"}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get("data", {}).get("list", [])
    except Exception as e:
        print(f"Erreur de connexion CJ : {e}")
    return []

def generate_update_stock_json():
    print("🤖 Synchronisation des produits et calcul du fret de base...")
    token = get_cj_access_token()
    if not token:
        print("❌ Token CJ introuvable.")
        return
    
    products_raw = fetch_cj_products_deep(token)
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
            poids_grammes = float(product.get("productWeight", 200))
        except ValueError:
            poids_grammes = 200.0

        # Frais de port de base calculés selon le poids réel du produit
        frais_port_base = round(3.00 + (poids_grammes * 0.0025), 2)

        product_obj = {
            "nom": nom,
            "tailles": tailles_values,
            "prix": prix_values,
            "images": images_values,
            "details": " | ".join(filter(None, details_list)),
            "stock": total_stock,
            "shippingBase": frais_port_base  # <-- Intégré directement dans le JSON
        }
        formatted_products.append(product_obj)

    with open("update_stock.json", "w", encoding="utf-8") as f:
        json.dump(formatted_products, f, ensure_ascii=False, indent=4)
    print("✨ Fichier update_stock.json généré avec succès pour GitHub Pages !")

if __name__ == "__main__":
    generate_update_stock_json()
