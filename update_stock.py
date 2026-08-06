import os
import json
import requests
from deep_translator import GoogleTranslator

# Configuration avec l'API Key moderne de CJ Dropshipping
CJ_API_KEY = os.environ.get("CJ_API_KEY")

def get_cj_access_token():
    url = "https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken"
    headers = {"Content-Type": "application/json"}
    
    if not CJ_API_KEY:
        print("❌ Erreur : La variable d'environnement CJ_API_KEY n'est pas définie dans les Secrets GitHub.")
        return None

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

def fetch_cj_products_stable(token):
    url = "https://developers.cjdropshipping.com/api2.0/v1/product/list"
    headers = {
        "CJ-Access-Token": token,
        "Content-Type": "application/json"
    }
    
    params = {
        "keyword": "women dress",
        "pageSize": 20
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get("result"):
                return data.get("data", {}).get("list", [])
    except Exception as e:
        print(f"Erreur lors de la récupération des produits : {e}")
        
    return []

def traduire_texte(texte):
    if not texte:
        return ""
    try:
        return GoogleTranslator(source='auto', target='fr').translate(texte)
    except Exception:
        return texte

def generate_update_stock_json():
    print("🤖 Démarrage du script stable et validé...")
    
    token = get_cj_access_token()
    if not token:
        print("❌ Impossible de continuer sans token CJ.")
        return

    products = fetch_cj_products_stable(token)
    if not products:
        print("⚠️ Aucun produit récupéré.")
        return

    formatted_products = []
    seen_skus = set()

    for product in products:
        sku = product.get("productSku") or product.get("sku")
        if not sku or sku in seen_skus:
            continue
        seen_skus.add(sku)

        # 1. Nom traduit
        nom_original = product.get("productName", "Produit sans titre")
        nom_traduite = traduire_texte(nom_original)

        # 2. Prix et Coûts
        sell_price = float(product.get("sellPrice", 0.0))
        product_fee = float(product.get("productFee", sell_price))
        shipping_cost = float(product.get("shippingCost", 8.10))

        # 3. Poids et Dimensions / Tailles / Couleurs
        poids_grammes = float(product.get("productWeight", 300))
        
        tailles = []
        couleurs = []
        variants_list = product.get("variants", [])
        
        if isinstance(variants_list, list):
            for v in variants_list:
                s = v.get("variantSize") or v.get("size")
                c = v.get("variantColor") or v.get("color")
                if s and s not in tailles:
                    tailles.append(s)
                if c and c not in couleurs:
                    couleurs.append(c)
                    
        if not tailles:
            tailles = ["Standard"]
        if not couleurs:
            couleurs = ["Unique"]

        # --- CALCULS LOGISTIQUES (France & US) ---
        if poids_grammes <= 300:
            port_base_fr = 8.10
        else:
            port_base_fr = 8.10 + ((poids_grammes - 300) * 0.0205)
        port_final_fr = port_base_fr + 0.99

        if poids_grammes <= 0.01:
            port_final_us = 6.67
        elif 1 <= poids_grammes <= 50:
            port_final_us = 7.73
        elif poids_grammes == 51:
            port_final_us = 7.76
        elif poids_grammes == 52:
            port_final_us = 7.78
        elif poids_grammes == 53:
            port_final_us = 7.80
        else:
            port_final_us = 7.80 + ((poids_grammes - 53) * 0.02)

        # Construction de l'objet final propre
        product_obj = {
            "dropshipping": "CJ Dropshipping",
            "sku": sku,
            "nom": nom_traduite,
            "prix": [sell_price],
            "tailles": tailles,
            "couleurs": couleurs,
            "productFee": round(product_fee, 2),
            "shippingCost": round(shipping_cost, 2),
            "images": [product.get("productImage", "")],
            "poids": poids_grammes,
            "shippingBase": round(port_final_fr, 2),
            "shippingUS": round(port_final_us, 2)
        }

        formatted_products.append(product_obj)

    if formatted_products:
        with open("update_stock.json", "w", encoding="utf-8") as f:
            json.dump(formatted_products, f, ensure_ascii=False, indent=4)
        print(f"🎉 Succès : {len(formatted_products)} produits enregistrés dans update_stock.json")
    else:
        print("⚠️ Aucun produit à enregistrer.")

if __name__ == "__main__":
    generate_update_stock_json()
