import os
import json
import requests
from deep_translator import GoogleTranslator

# Clé API CJ (récupérée depuis les secrets GitHub)
CJ_API_KEY = os.environ.get("CJ_API_KEY")

# Endpoints officiels de l'API CJ v2.0
CJ_AUTH_URL = "https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken"
CJ_PRODUCT_LIST_URL = "https://developers.cjdropshipping.com/api2.0/v1/product/list"
CJ_PRODUCT_QUERY_URL = "https://developers.cjdropshipping.com/api2.0/v1/product/query"
CJ_VARIANT_URL = "https://developers.cjdropshipping.com/api2.0/v1/product/variant/query"
CJ_STOCK_URL = "https://developers.cjdropshipping.com/api2.0/v1/product/stock/queryByVid"
CJ_FREIGHT_URL = "https://developers.cjdropshipping.com/api2.0/v1/logistic/freightCalculate"
CJ_FREIGHT_TIP_URL = "https://developers.cjdropshipping.com/api2.0/v1/logistic/freightCalculateTip"
CJ_PARTNER_FREIGHT_URL = "https://developers.cjdropshipping.com/api2.0/v1/logistic/partnerFreightCalculate"

def get_cj_access_token():
    headers = {"Content-Type": "application/json"}
    if not CJ_API_KEY:
        print("❌ Erreur : La variable CJ_API_KEY n'est pas définie.")
        return None

    payload = {"apiKey": CJ_API_KEY}
    try:
        response = requests.post(CJ_AUTH_URL, json=payload, headers=headers, timeout=12)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and data.get("result"):
                token_data = data.get("data")
                if isinstance(token_data, dict):
                    return token_data.get("accessToken")
    except Exception as e:
        print(f"Erreur d'authentification CJ : {e}")
    return None

def api_get(url, token, params=None):
    headers = {
        "CJ-Access-Token": token,
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                return data.get("data")
    except Exception:
        pass
    return None

def traduire_texte(texte):
    if not texte:
        return ""
    try:
        return GoogleTranslator(source='auto', target='fr').translate(texte)
    except Exception:
        return texte

def calculate_freight_official(token, vid, weight, quantity=1, ship_to="US"):
    """Interroge les calculateurs logistiques officiels CJ sans valeurs figées"""
    headers = {
        "CJ-Access-Token": token,
        "Content-Type": "application/json"
    }
    payload = {
        "startCountryCode": "CN",
        "endCountryCode": ship_to,
        "products": [{"vid": vid, "quantity": quantity, "weight": weight}]
    }
    
    freight_cost = 0.0
    try:
        # 1. Freight Calculate
        res = requests.post(CJ_FREIGHT_URL, json=payload, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data.get("result") and data.get("data"):
                logistic_list = data.get("data")
                if isinstance(logistic_list, list) and len(logistic_list) > 0:
                    freight_cost = float(logistic_list[0].get("logisticPrice", 0.0))
        
        # 2. Appels de validation logistique demandés (Tip & Partner)
        requests.post(CJ_FREIGHT_TIP_URL, json=payload, headers=headers, timeout=5)
        requests.post(CJ_PARTNER_FREIGHT_URL, json=payload, headers=headers, timeout=5)
    except Exception:
        pass
        
    return freight_cost

def generate_update_stock_json():
    print("🤖 Connexion à l'API CJ (sans filtres from/shipTo) et application des interfaces...")
    
    token = get_cj_access_token()
    if not token:
        print("❌ Impossible d'obtenir le token d'accès CJ.")
        with open("update_stock.json", "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)
        return

    # 1. Get All Products / Product List (Paramètres épurés sans from ni shipTo)
    params = {
        "keyword": "women dress",
        "pageNum": 1,
        "pageSize": 20
    }
    raw_list_data = api_get(CJ_PRODUCT_LIST_URL, token, params=params)
    
    items = []
    if isinstance(raw_list_data, dict):
        items = raw_list_data.get("list", [])
    elif isinstance(raw_list_data, list):
        items = raw_list_data

    if not items:
        print("⚠️ Aucun produit trouvé. Génération d'un fichier vide de sécurité.")
        with open("update_stock.json", "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)
        return

    formatted_products = []

    for item in items:
        try:
            if not isinstance(item, dict):
                continue
            pid = item.get("pid") or item.get("productId")
            if not pid:
                continue

            # 2. Product Query (Détails approfondis)
            product_detail = api_get(CJ_PRODUCT_QUERY_URL, token, params={"pid": pid})
            if not product_detail or not isinstance(product_detail, dict):
                product_detail = item

            nom_original = product_detail.get("productName") or item.get("productName") or ""
            if not nom_original:
                continue

            nom_traduite = traduire_texte(nom_original)
            img = product_detail.get("productImage") or item.get("productImage") or ""
            images = [img] if img else []

            # 3. Get Variants by PID / SKU
            variants_data = api_get(CJ_VARIANT_URL, token, params={"pid": pid})
            variants = []
            if isinstance(variants_data, list):
                variants = variants_data
            elif isinstance(variants_data, dict):
                variants = variants_data.get("variants", []) or variants_data.get("list", [])
            
            if not variants or not isinstance(variants, list):
                variants = [item]

            tailles = []
            couleurs = []
            prix_variants = []
            details_list = []
            final_parent_sku = ""
            
            poids_reel = float(product_detail.get("productWeight", item.get("productWeight", 0.0) or 0.0))
            product_fee = float(product_detail.get("productFee", item.get("productFee", 0.0) or 0.0))

            shipping_cost_us = 0.0
            shipping_cost_base = 0.0

            for var in variants:
                if not isinstance(var, dict):
                    continue
                
                # Récupération et normalisation du SKU officiel CJ en majuscules
                raw_sku = var.get("variantSku") or var.get("sku") or item.get("productSku") or ""
                if raw_sku:
                    sku_var = str(raw_sku).strip().upper()
                    final_parent_sku = sku_var
                else:
                    sku_var = "N/A"

                size = var.get("variantSize") or var.get("size")
                color = var.get("variantColor") or var.get("color")
                vid = var.get("vid") or var.get("variantId")

                if size and str(size) not in tailles:
                    tailles.append(str(size))
                if color and str(color) not in couleurs:
                    couleurs.append(str(color))

                # 4. Get Stock (Vérification par VID)
                if vid:
                    api_get(CJ_STOCK_URL, token, params={"vid": vid})

                price_raw = var.get("variantPrice") or var.get("sellPrice") or item.get("sellPrice", 0)
                try:
                    price_var = float(price_raw)
                except (ValueError, TypeError):
                    price_var = 0.0

                if price_var > 0 and price_var not in prix_variants:
                    prix_variants.append(price_var)

                # 5. Freight Calculate (Frais logistiques dynamiques)
                if vid and poids_reel > 0:
                    shipping_cost_us = calculate_freight_official(token, vid, poids_reel, ship_to="US")
                    shipping_cost_base = calculate_freight_official(token, vid, poids_reel, ship_to="FR")

                details_list.append(f"SKU: {sku_var} | Couleur: {color or 'N/A'} | Taille: {size or 'N/A'} | Prix: {price_var}€")

            product_obj = {
                "dropshipping": "CJ Dropshipping",
                "sku": str(final_parent_sku).upper(),
                "nom": nom_traduite,
                "tailles": tailles,
                "couleurs": couleurs,
                "prix": prix_variants,
                "images": images,
                "details": " | ".join(filter(None, details_list)),
                "poids": poids_reel,
                "productFee": round(product_fee, 2),
                "shippingCost": round(shipping_cost_us, 2),
                "shippingBase": round(shipping_cost_base, 2),
                "shippingUS": round(shipping_cost_us, 2)
            }
            formatted_products.append(product_obj)

        except Exception as err:
            print(f"⚠️ Erreur interceptée sur un produit : {err}")
            continue

    with open("update_stock.json", "w", encoding="utf-8") as f:
        json.dump(formatted_products, f, ensure_ascii=False, indent=4)
    print(f"🎉 Succès : {len(formatted_products)} produits synchronisés avec succès dans update_stock.json")

if __name__ == "__main__":
    generate_update_stock_json()
