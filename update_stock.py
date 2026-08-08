import os
import json
import requests
from deep_translator import GoogleTranslator

CJ_API_KEY = os.environ.get("CJ_API_KEY")

def get_cj_access_token():
    url = "https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken"
    headers = {"Content-Type": "application/json"}
    
    if not CJ_API_KEY:
        print("❌ Erreur : La variable CJ_API_KEY n'est pas définie.")
        return None

    payload = {"apiKey": CJ_API_KEY}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=12)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and data.get("result"):
                token_data = data.get("data")
                if isinstance(token_data, dict):
                    return token_data.get("accessToken")
    except Exception as e:
        print(f"Erreur d'authentification CJ : {e}")
    return None

def fetch_cj_product_variants(token, pid):
    url = "https://developers.cjdropshipping.com/api2.0/v1/product/variant"
    headers = {
        "CJ-Access-Token": token,
        "Content-Type": "application/json"
    }
    params = {"pid": pid}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=12)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and data.get("result"):
                return data.get("data")
    except Exception:
        pass
    return None

def search_cj_products_strict(token):
    # Endpoint officiel de l'API CJ simulant la recherche basée sur votre lien
    url = "https://developers.cjdropshipping.com/api2.0/v1/product/list"
    headers = {
        "CJ-Access-Token": token,
        "Content-Type": "application/json"
    }
    # Paramètres basés exactement sur votre lien de recherche (women dress, CN -> US)
    params = {
        "keyword": "women dress",
        "pageNum": 1,
        "pageSize": 20,
        "from": "CN",
        "shipTo": "US"
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=12)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                inner_data = data.get("data")
                if isinstance(inner_data, dict):
                    items = inner_data.get("list", [])
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
    print("🤖 Connexion à l'API CJ et recherche via le lien configuré (women dress, CN -> US)...")
    
    token = get_cj_access_token()
    if not token:
        print("❌ Impossible d'obtenir le token d'accès CJ.")
        return

    raw_products = search_cj_products_strict(token)
    if not raw_products:
        print("⚠️ Aucun produit brut récupéré, création d'un fichier de secours vide pour éviter les erreurs Git.")
        with open("update_stock.json", "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)
        return

    formatted_products = []
    seen_skus = set()

    for product in raw_products:
        try:
            if not isinstance(product, dict):
                continue
                
            pid = product.get("pid")
            raw_sku = product.get("productSku") or product.get("sku") or product.get("entrySku") or ""
            
            if not pid:
                continue

            # Inspection approfondie pour récupérer les variantes et les vrais détails
            detailed_data = fetch_cj_product_variants(token, pid)
            if not detailed_data or not isinstance(detailed_data, dict):
                detailed_data = product

            nom_original = detailed_data.get("productName") or product.get("productName") or ""
            if not nom_original:
                continue

            nom_traduite = traduire_texte(nom_original)
            
            variants = detailed_data.get("variants", [])
            if not variants or not isinstance(variants, list):
                variants = [product]

            tailles = []
            couleurs = []
            prix_variants = []
            details_list = []
            
            img = detailed_data.get("productImage") or product.get("productImage") or ""
            images = [img] if img else []
            
            poids_reel = product.get("productWeight", 0.0)
            try:
                poids_reel = float(poids_reel)
            except (ValueError, TypeError):
                poids_reel = 0.0

            product_fee = product.get("productFee", 0.0)
            shipping_cost = product.get("shippingCost", 0.0)

            final_parent_sku = raw_sku

            for var in variants:
                if not isinstance(var, dict):
                    continue
                    
                sku_var = var.get("variantSku") or var.get("sku") or raw_sku
                if sku_var:
                    # Normalisation stricte du SKU en majuscules (ex: CJYD...IR)
                    sku_var = str(sku_var).strip().upper()
                    final_parent_sku = sku_var
                    seen_skus.add(sku_var)
                    
                size = var.get("variantSize") or var.get("size")
                color = var.get("variantColor") or var.get("color")
                
                if size and str(size) not in tailles:
                    tailles.append(str(size))
                if color and str(color) not in couleurs:
                    couleurs.append(str(color))
                    
                price_raw = var.get("variantPrice") or var.get("sellPrice") or product.get("sellPrice", 0)
                try:
                    price_var = float(price_raw)
                except (ValueError, TypeError):
                    price_var = 0.0
                    
                if price_var > 0 and price_var not in prix_variants:
                    prix_variants.append(price_var)

                details_list.append(f"SKU: {sku_var} | Couleur: {color or 'N/A'} | Taille: {size or 'N/A'} | Prix: {price_var}€")

            # Conversion du poids si nécessaire
            if 0 < poids_reel < 10:
                poids_grammes = poids_reel * 1000
            else:
                poids_grammes = poids_reel

            # Calculs logistiques
            if poids_grammes <= 300:
                port_base_fr = 8.10
            else:
                port_base_fr = 8.10 + ((poids_grammes - 300) * 0.0205)
            port_final_fr = port_base_fr + 0.99

            port_final_us = 7.73 if poids_grammes <= 50 else 7.80 + max(0, (poids_grammes - 53) * 0.02)

            product_obj = {
                "dropshipping": "CJ Dropshipping",
                "sku": str(final_parent_sku).upper(),
                "nom": nom_traduite,
                "tailles": tailles,
                "couleurs": couleurs,
                "prix": prix_variants,
                "images": images,
                "details": " | ".join(filter(None, details_list)),
                "poids": float(poids_reel),
                "productFee": round(float(product_fee), 2),
                "shippingCost": round(float(shipping_cost), 2),
                "shippingBase": round(port_final_fr, 2),
                "shippingUS": round(port_final_us, 2)
            }
            formatted_products.append(product_obj)

        except Exception as err:
            print(f"⚠️ Erreur interceptée sur un produit : {err}")
            continue

    # Écriture systématique du fichier JSON pour éviter l'erreur Git pathspec
    with open("update_stock.json", "w", encoding="utf-8") as f:
        json.dump(formatted_products, f, ensure_ascii=False, indent=4)
    print(f"🎉 Succès : {len(formatted_products)} produits synchronisés avec SKU officiels en majuscules dans update_stock.json")

if __name__ == "__main__":
    generate_update_stock_json()
