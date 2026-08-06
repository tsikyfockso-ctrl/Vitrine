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

def verify_and_get_strict_product(token, target_sku):
    """
    Simule la vérification humaine : interroge l'API CJ avec le SKU exact 
    pour confirmer que le produit existe bel et bien.
    """
    if not target_sku or target_sku == "N/A":
        return None
        
    url = "https://developers.cjdropshipping.com/api2.0/v1/product/query"
    headers = {
        "CJ-Access-Token": token,
        "Content-Type": "application/json"
    }
    params = {"productSku": target_sku}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            product_data = data.get("data")
            if data.get("result") and product_data:
                # Vérification que le SKU retourné correspond parfaitement au SKU cherché
                if isinstance(product_data, dict):
                    found_sku = product_data.get("productSku") or product_data.get("sku")
                    if found_sku and found_sku.strip() == target_sku.strip():
                        return product_data
                elif isinstance(product_data, list) and len(product_data) > 0:
                    for item in product_data:
                        found_sku = item.get("productSku") or item.get("sku")
                        if found_sku and found_sku.strip() == target_sku.strip():
                            return item
    except Exception:
        pass
        
    return None

def search_cj_like_human(token):
    """
    Imite un humain tapant 'women dress' dans la barre de recherche du site CJ.
    """
    url = "https://developers.cjdropshipping.com/api2.0/v1/product/list"
    headers = {
        "CJ-Access-Token": token,
        "Content-Type": "application/json"
    }
    
    # Recherche exacte avec le mot-clé demandé
    params = {
        "keyword": "women dress",
        "pageSize": 30
    }
    
    print("🔍 Action humaine : Saisie de 'women dress' dans la barre de recherche CJ...")
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            products = data.get("data", {}).get("list", [])
            print(f"📦 {len(products)} produits trouvés dans les résultats de recherche.")
            return products
    except Exception as e:
        print(f"Erreur lors de la recherche CJ : {e}")
        
    return []

def traduire_texte(texte):
    """Traduit automatiquement n'importe quel texte en Français"""
    if not texte:
        return ""
    try:
        return GoogleTranslator(source='auto', target='fr').translate(texte)
    except Exception:
        return texte

def generate_update_stock_json():
    print("🤖 Démarrage du script intelligent (Recherche ciblée 'women dress' + Validation SKU)...")
    
    token = get_cj_access_token()
    if not token:
        print("❌ Erreur : Impossible d'obtenir le token d'accès CJ.")
        return

    # 1. Recherche par mot-clé comme un humain
    products_raw = search_cj_like_human(token)
    
    formatted_products = []
    seen_skus = set()

    # 2. Analyse un par un des produits de la liste
    for product in products_raw:
        sku = product.get("productSku") or product.get("sku") or "N/A"
        
        if sku in seen_skus or sku == "N/A":
            continue
            
        print(f"👉 Inspection du produit -> SKU testé : {sku}")
        
        # 3. Test unitaire rigoureux du SKU pour s'assurer qu'il est valide
        verified_product = verify_and_get_strict_product(token, sku)
        
        if not verified_product:
            print(f"❌ SKU {sku} non validé/introuvable. Le produit est ignoré.")
            continue
            
        print(f"✅ SKU {sku} validé avec succès !")
        seen_skus.add(sku)
        
        # Récupération et traduction des données validées
        nom_original = verified_product.get("productName", product.get("productName", "Produit sans titre"))
        nom_traduite = traduire_texte(nom_original)
        
        poids_brut = verified_product.get("productWeight", product.get("productWeight", 200))
        try:
            poids_grammes = float(product.get("productWeight", 200))
        except ValueError:
            poids_grammes = 200.0

        # --- TARIF DE LIVRAISON : FRANCE (FR) ---
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

        # --- TARIF DE LIVRAISON : ÉTATS-UNIS (US) ---
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

        product_obj = {
            "sku": sku,
            "nom": nom_traduite,
            "prix": verified_product.get("sellPrice", product.get("sellPrice", 0.0)),
            "images": [verified_product.get("productImage", product.get("productImage", ""))],
            "poids": poids_grammes,
            "shippingBase": round(port_final_fr, 2),
            "shippingUS": round(port_final_us, 2)
        }
        formatted_products.append(product_obj)

    # 4. Enregistrement dans le fichier final
    if formatted_products:
        with open("update_stock.json", "w", encoding="utf-8") as f:
            json.dump(formatted_products, f, ensure_ascii=False, indent=4)
        print(f"🎉 Succès total : {len(formatted_products)} robes authentiques et vérifiées enregistrées dans update_stock.json")
    else:
        print("⚠️ Aucun produit n'a validé le test SKU.")

if __name__ == "__main__":
    generate_update_stock_json()
