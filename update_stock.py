import os
import json
import requests
from deep_translator import GoogleTranslator

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

def fetch_product_details_and_variants(token, pid):
    """
    Simule le clic sur un produit pour récupérer les variantes détaillées,
    les tailles, les couleurs, les prix et les détails de coûts (Product Fee / Shipping Cost).
    """
    url = "https://developers.cjdropshipping.com/api2.0/v1/product/variant"
    headers = {
        "CJ-Access-Token": token,
        "Content-Type": "application/json"
    }
    params = {"pid": pid}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get("result"):
                return data.get("data")
    except Exception as e:
        print(f"Erreur lors de la récupération des détails pour le PID {pid} : {e}")
        
    return None

def search_cj_products(token):
    """
    Recherche les produits sur la barre de recherche CJ avec le mot-clé 'women dress'
    """
    url = "https://developers.cjdropshipping.com/api2.0/v1/product/list"
    headers = {
        "CJ-Access-Token": token,
        "Content-Type": "application/json"
    }
    params = {
        "keyword": "women dress",
        "pageSize": 15
    }
    
    print("🔍 Recherche ciblée sur la barre CJ avec le mot-clé : 'women dress'...")
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            products = data.get("data", {}).get("list", [])
            print(f"📦 {len(products)} produits trouvés dans les résultats.")
            return products
    except Exception as e:
        print(f"Erreur de recherche CJ : {e}")
    return []

def traduire_texte(texte):
    if not texte:
        return ""
    try:
        return GoogleTranslator(source='auto', target='fr').translate(texte)
    except Exception:
        return texte

def generate_update_stock_json():
    print("🤖 Démarrage du script d'extraction intelligente (Variantes, Tailles, Couleurs, Product Fee & Shipping Cost)...")
    
    token = get_cj_access_token()
    if not token:
        print("❌ Erreur : Impossible d'obtenir le token d'accès CJ.")
        return

    # 1. Recherche par mot-clé
    raw_products = search_cj_products(token)
    formatted_products = []
    seen_skus = set()

    for product in raw_products:
        pid = product.get("pid")
        parent_sku = product.get("productSku") or product.get("sku")
        
        if not pid or parent_sku in seen_skus:
            continue
            
        print(f"\n👉 Inspection détaillée du produit PID: {pid} (SKU: {parent_sku})")
        
        # 2 & 5 & 6 & 7. Récupération des variantes, des prix, tailles, couleurs et coûts détaillés
        detailed_data = fetch_product_details_and_variants(token, pid)
        if not detailed_data:
            print(f"⚠️ Impossible de récupérer les détails/variantes pour le PID {pid}.")
            continue
            
        # Extraction des informations de base
        nom_original = detailed_data.get("productName", product.get("productName", "Produit sans titre"))
        nom_traduite = traduire_texte(nom_original)
        
        variants = detailed_data.get("variants", [])
        if not variants:
            # S'il n'y a pas de tableau de variantes détaillé, on utilise les données de base
            variants = [product]

        tailles_values = []
        prix_values = []
        couleurs_values = []
        details_list = []
        images_values = [detailed_data.get("productImage", product.get("productImage", ""))]
        
        total_poids = 300.0
        product_fee = 0.0
        shipping_cost = 0.0

        for var in variants:
            sku_var = var.get("variantSku") or var.get("sku")
            if sku_var:
                seen_skus.add(sku_var)
                
            # Récupération des attributs (Taille / Couleur)
            size = var.get("variantSize") or var.get("size") or ""
            color = var.get("variantColor") or var.get("color") or ""
            
            if size and size not in tailles_values:
                tailles_values.append(size)
            if color and color not in couleurs_values:
                couleurs_values.append(color)
                
            # Prix par variante
            price_var = var.get("variantPrice") or var.get("sellPrice") or product.get("sellPrice", 0.0)
            try:
                price_var = float(price_var)
            except ValueError:
                price_var = 0.0
            if price_var not in prix_values:
                prix_values.append(price_var)
                
            # Poids par variante (si disponible)
            weight_var = var.get("variantWeight") or product.get("productWeight", 300)
            try:
                total_poids = float(weight_var)
            except (ValueError, TypeError):
                pass

            # Récupération des détails de coûts (Product Fee & Shipping Cost)
            product_fee = float(var.get("productFee", product.get("productFee", price_var)))
            shipping_cost = float(var.get("shippingCost", product.get("shippingCost", 8.10)))

            details_list.append(f"SKU: {sku_var} | Couleur: {color or 'Unique'} | Taille: {size or 'Unique'} | Prix: {price_var}€")

        # Calculs logistiques (France et États-Unis basés sur le poids)
        if total_poids <= 300:
            port_base_fr = 8.10
        else:
            port_base_fr = 8.10 + ((total_poids - 300) * 0.0205)
        port_final_fr = port_base_fr + 0.99

        if total_poids <= 0.01:
            port_final_us = 6.67
        elif 1 <= total_poids <= 50:
            port_final_us = 7.73
        elif total_poids == 51:
            port_final_us = 7.76
        elif total_poids == 52:
            port_final_us = 7.78
        elif total_poids == 53:
            port_final_us = 7.80
        else:
            port_final_us = 7.80 + ((total_poids - 53) * 0.02)

        # Construction de l'objet complet structuré
        product_obj = {
            "sku": parent_sku,
            "nom": nom_traduite,
            "tailles": tailles_values,
            "couleurs": couleurs_values,
            "prix": prix_values if prix_values else [0.0],
            "images": images_values,
            "details": " | ".join(filter(None, details_list)),
            "poids": total_poids,
            "productFee": round(product_fee, 2),     # Coût du produit extrait des détails
            "shippingCost": round(shipping_cost, 2), # Frais d'expédition de base extraits
            "shippingBase": round(port_final_fr, 2), # Frais de port calculés pour la France
            "shippingUS": round(port_final_us, 2)    # Frais de port calculés pour les USA
        }
        
        formatted_products.append(product_obj)
        print(f"✅ Succès : Produit '{nom_traduite}' extrait avec {len(tailles_values)} tailles, {len(couleurs_values)} couleurs et ses coûts détaillés.")

    if formatted_products:
        with open("update_stock.json", "w", encoding="utf-8") as f:
            json.dump(formatted_products, f, ensure_ascii=False, indent=4)
        print(f"\n🎉 Terminé ! {len(formatted_products)} produits intelligents enregistrés dans update_stock.json")
    else:
        print("⚠️ Aucun produit n'a pu être extrait.")

if __name__ == "__main__":
    generate_update_stock_json()
