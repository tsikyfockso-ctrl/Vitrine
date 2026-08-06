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
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get("result"):
                return data.get("data", {}).get("accessToken")
    except Exception as e:
        print(f"Erreur d'authentification CJ : {e}")
    return None

def fetch_product_details_and_variants(token, pid):
    """Récupère les variantes en toute sécurité"""
    url = "https://developers.cjdropshipping.com/api2.0/v1/product/variant"
    headers = {
        "CJ-Access-Token": token,
        "Content-Type": "application/json"
    }
    params = {"pid": pid}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get("result"):
                return data.get("data")
    except Exception:
        pass
    return None

def search_cj_products(token):
    """Recherche les produits sur la barre de recherche CJ"""
    url = "https://developers.cjdropshipping.com/api2.0/v1/product/list"
    headers = {
        "CJ-Access-Token": token,
        "Content-Type": "application/json"
    }
    params = {
        "keyword": "women dress",
        "pageSize": 15
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            items = data.get("data", {}).get("list", [])
            return items if isinstance(items, list) else []
    except Exception:
        pass
    return []

def traduire_texte(texte):
    if not texte:
        return ""
    try:
        return GoogleTranslator(source='auto', target='fr').translate(texte)
    except Exception:
        return texte

def generate_update_stock_json():
    print("🤖 Démarrage du script blindé anti-erreur (Variantes, Tailles, Couleurs & Coûts)...")
    
    token = get_cj_access_token()
    if not token:
        print("❌ Erreur : Impossible d'obtenir le token d'accès CJ.")
        return

    raw_products = search_cj_products(token)
    if not raw_products:
        print("⚠️ Aucun produit brut récupéré depuis l'API CJ.")
        return

    formatted_products = []
    seen_skus = set()

    for product in raw_products:
        try:
            if not isinstance(product, dict):
                continue
                
            pid = product.get("pid")
            parent_sku = product.get("productSku") or product.get("sku") or "N/A"
            
            if not pid or parent_sku in seen_skus:
                continue
                
            # Récupération détaillée ou fallback sur le produit de base
            detailed_data = fetch_product_details_and_variants(token, pid)
            if not detailed_data or not isinstance(detailed_data, dict):
                detailed_data = product
                
            nom_original = detailed_data.get("productName") or product.get("productName") or "Produit sans titre"
            nom_traduite = traduire_texte(nom_original)
            
            variants = detailed_data.get("variants", [])
            if not variants or not isinstance(variants, list):
                variants = [product]

            tailles_values = []
            prix_values = []
            couleurs_values = []
            details_list = []
            
            img_base = detailed_data.get("productImage") or product.get("productImage") or ""
            images_values = [img_base] if img_base else []
            
            total_poids = 300.0
            product_fee = 0.0
            shipping_cost = 0.0

            for var in variants:
                if not isinstance(var, dict):
                    continue
                    
                sku_var = var.get("variantSku") or var.get("sku") or parent_sku
                if sku_var:
                    seen_skus.add(sku_var)
                    
                size = var.get("variantSize") or var.get("size") or ""
                color = var.get("variantColor") or var.get("color") or ""
                
                if size and size not in tailles_values:
                    tailles_values.append(str(size))
                if color and color not in couleurs_values:
                    couleurs_values.append(str(color))
                    
                price_raw = var.get("variantPrice") or var.get("sellPrice") or product.get("sellPrice") or 0.0
                try:
                    price_var = float(price_raw)
                except (ValueError, TypeError):
                    price_var = 0.0
                    
                if price_var not in prix_values:
                    prix_values.append(price_var)
                    
                weight_raw = var.get("variantWeight") or product.get("productWeight") or 300
                try:
                    total_poids = float(weight_raw) if weight_raw else 300.0
                except (ValueError, TypeError):
                    pass

                try:
                    product_fee = float(var.get("productFee") or product.get("productFee") or price_var)
                except (ValueError, TypeError):
                    product_fee = price_var

                try:
                    shipping_cost = float(var.get("shippingCost") or product.get("shippingCost") or 8.10)
                except (ValueError, TypeError):
                    shipping_cost = 8.10

                details_list.append(f"SKU: {sku_var} | Couleur: {color or 'Unique'} | Taille: {size or 'Unique'} | Prix: {price_var}€")

            # Calculs logistiques sécurisés
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

            product_obj = {
                "sku": parent_sku,
                "nom": nom_traduite,
                "tailles": tailles_values,
                "couleurs": couleurs_values,
                "prix": prix_values if prix_values else [0.0],
                "images": images_values,
                "details": " | ".join(filter(None, details_list)),
                "poids": total_poids,
                "productFee": round(product_fee, 2),
                "shippingCost": round(shipping_cost, 2),
                "shippingBase": round(port_final_fr, 2),
                "shippingUS": round(port_final_us, 2)
            }
            formatted_products.append(product_obj)
            
        except Exception as err:
            print(f"⚠️ Un produit a rencontré une anomalie et a été ignoré en toute sécurité : {err}")
            continue

    if formatted_products:
        with open("update_stock.json", "w", encoding="utf-8") as f:
            json.dump(formatted_products, f, ensure_ascii=False, indent=4)
        print(f"🎉 Succès : {len(formatted_products)} produits formatés et enregistrés dans update_stock.json")
    else:
        print("⚠️ Aucun produit valide n'a pu être extrait.")

if __name__ == "__main__":
    generate_update_stock_json()
