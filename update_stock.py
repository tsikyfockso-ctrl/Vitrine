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
    print("🤖 Synchronisation avec les données et application des tarifs de transport...")
    
    token = get_cj_access_token()
    if not token:
        print("❌ Impossible d'obtenir le token d'accès CJ.")
        return

    products_raw = fetch_cj_products_deep(token)
    processed_products = []

    for product in products_raw:
        nom = product.get("productName", "Produit sans nom")
        
        # Gestion des variantes / prix / stock
        variants = product.get("variants", [])
        tailles_values = []
        prix_values = []
        images_values = []
        total_stock = 0
        details_list = []

        if variants:
            for v in variants:
                tailles_values.append(v.get("variantName", ""))
                prix_values.append(str(v.get("variantPrice", "0")))
                images_values.append(v.get("variantImage", ""))
                total_stock += int(v.get("variantStock", 0))
        else:
            tailles_values.append("Standard")
            prix_values.append(str(product.get("sellPrice", "0")))
            images_values.append(product.get("productImage", ""))
            total_stock = product.get("totalStock", 100)

        # Récupération du poids du produit en grammes
        try:
            poids_grammes = float(product.get("productWeight", 200))
        except ValueError:
            poids_grammes = 200.0

        # --- 1. TARIF DE LIVRAISON : FRANCE (FR) ---
        if poids_grammes <= 1:
            port_base_fr = 3.54
        elif poids_grammes < 100:
            port_base_fr = 3.54 + (poids_grammes * 0.015)
        elif poids_grammes == 100:
            port_base_fr = 4.05
        elif poids_grammes <= 300:
            port_base_fr = 4.05 + ((poids_grammes - 100) * 0.02525)
        else:
            port_base_fr = 8.10 + ((poids_grammes - 300) * 0.0205)

        port_final_fr = port_base_fr + 0.99

        # --- 2. TARIF DE LIVRAISON : ÉTATS-UNIS (US) ---
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
            # Application de la règle de +0.02 par gramme supplémentaire au-delà de 53g
            port_final_us = 7.80 + ((poids_grammes - 53) * 0.02)

        # Construction de l'objet produit final pour le fichier JSON
        product_obj = {
            "nom": nom,
            "tailles": tailles_values,
            "prix": prix_values,
            "images": images_values,
            "details": " | ".join(filter(None, details_list)),
            "stock": total_stock,
            "poids": poids_grammes,
            "shippingBase": round(port_final_fr, 2), # Utilisé pour la France
            "shippingUS": round(port_final_us, 2)    # Utilisé pour les États-Unis
        }
        processed_products.append(product_obj)

    # Écriture dans le fichier JSON local
    with open("update_stock.json", "w", encoding="utf-8") as f:
        json.dump(processed_products, f, ensure_ascii=False, indent=4)

    print(f"✅ Succès : {len(processed_products)} produits synchronisés dans update_stock.json")

if __name__ == "__main__":
    generate_update_stock_json()
