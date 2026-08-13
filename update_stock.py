import os
import json
import requests
from deep_translator import GoogleTranslator

# Clé API CJ (récupérée depuis les secrets GitHub)
CJ_API_KEY = os.environ.get("CJ_API_KEY")

# URLs officielles de l'API CJ V2.0
CJ_AUTH_URL = "https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken"
CJ_PRODUCT_LIST_URL = "https://developers.cjdropshipping.com/api2.0/v1/product/listV2"
CJ_PRODUCT_QUERY_URL = "https://developers.cjdropshipping.com/api2.0/v1/product/query"
CJ_PRODUCT_VARIANT_URL = "https://developers.cjdropshipping.com/api2.0/v1/product/variant/queryByVid"
CJ_FREIGHT_URL = "https://developers.cjdropshipping.com/api2.0/v1/logistic/freightCalculate"
CJ_FREIGHT_TIP_URL = "https://developers.cjdropshipping.com/api2.0/v1/logistic/freightCalculateTip"
CJ_PARTNER_FREIGHT_URL = "https://developers.cjdropshipping.com/api2.0/v1/logistic/partnerFreightCalculate"

# Dictionnaire de secours élargi pour éviter les retours vides sur 'Lady Dress'
CATEGORIES_SECOURS = [
    {"keyword": "Lady Dress", "categoryId": "D2432903-0D4E-4787-886F-D3D9DA7890D9"},
]

def get_cj_access_token():
    headers = {"Content-Type": "application/json"}
    if not CJ_API_KEY:
        print("❌ Erreur : La variable CJ_API_KEY n'est pas définie.")
        return None

    payload = {"apiKey": CJ_API_KEY}
    try:
        response = requests.post(CJ_AUTH_URL, json=payload, headers=headers, timeout=60)
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

def nettoyer_texte(val):
    if not val:
        return ""
    if isinstance(val, list):
        val = val[0] if val else ""
    val_str = str(val).strip()
    
    if val_str.startswith("[") and val_str.endswith("]"):
        try:
            parsed = json.loads(val_str)
            if isinstance(parsed, list) and len(parsed) > 0:
                val_str = str(parsed[0])
        except Exception:
            pass
            
    return val_str.strip('[]"\'')

def traduire_texte(texte):
    texte_propre = nettoyer_texte(texte)
    if not texte_propre:
        return ""
    try:
        trads = GoogleTranslator(source='auto', target='fr').translate(texte_propre)
        return nettoyer_texte(trads)
    except Exception:
        return texte_propre

def safe_float(val):
    if val is None:
        return 0.0
    val_str = str(val).strip()
    if "-" in val_str and not val_str.startswith("-"):
        val_str = val_str.split("-")[0].strip()
    try:
        return float(val_str)
    except (ValueError, TypeError):
        return 0.0

def calculate_logistics(token, vid, weight, ship_to="US"):
    headers = {
        "CJ-Access-Token": token,
        "Content-Type": "application/json"
    }
    payload = {
        "startCountryCode": "CN",
        "endCountryCode": ship_to,
        "products": [{"vid": vid, "quantity": 1, "weight": weight}]
    }
    
    freight_cost = 0.0
    try:
        res = requests.post(CJ_FREIGHT_URL, json=payload, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data.get("result") and data.get("data"):
                logistic_list = data.get("data")
                if isinstance(logistic_list, list) and len(logistic_list) > 0:
                    freight_cost = safe_float(logistic_list[0].get("logisticPrice", 0.0))
        
        requests.post(CJ_FREIGHT_TIP_URL, json=payload, headers=headers, timeout=5)
        requests.post(CJ_PARTNER_FREIGHT_URL, json=payload, headers=headers, timeout=5)
    except Exception:
        pass
        
    return freight_cost

def generate_update_stock_json():
    print("🤖 Exécution de listV2 pour la mise à jour des stocks et des produits...")
    
    token = get_cj_access_token()
    if not token:
        print("❌ Impossible d'obtenir le token d'accès.")
        with open("update_stock.json", "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)
        return

    items = []

    for cat in CATEGORIES_SECOURS:
        kw = cat["keyword"]
        cat_id = cat["categoryId"]
        raw_response = None
        
        if kw:
            params = {"page": 1, "size": 20, "keyWord": kw}
            print(f"🔍 Essai de recherche par mot-clé : '{kw}'")
            raw_response = api_get(CJ_PRODUCT_LIST_URL, token, params=params)

        if not raw_response and cat_id:
            params_cat = {"page": 1, "size": 20, "categoryId": cat_id}
            print(f"⚠️ Aucun résultat pour '{kw}', basculement sur le categoryId : {cat_id}")
            raw_response = api_get(CJ_PRODUCT_LIST_URL, token, params=params_cat)

        if raw_response and isinstance(raw_response, dict):
            temp_items = raw_response.get("productList", [])
            if temp_items:
                print(f"✅ {len(temp_items)} produits trouvés dans productList avec le critère '{kw or cat_id}' !")
                items = temp_items
                break

    if not items:
        print("⚠️ Aucun produit trouvé après tous les essais de secours.")
        with open("update_stock.json", "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)
        return

    formatted_products = []

    for item in items:
        try:
            if not isinstance(item, dict):
                continue
            
            pid = (
                item.get("id") or 
                item.get("pid") or 
                item.get("productId") or 
                item.get("productDid") or 
                item.get("productID") or
                item.get("goodsId") or
                item.get("uuid")
            )
            
            if not pid:
                continue
            
            print(f"🔍 Traitement PID extrait : {pid}")

            product_detail = api_get(CJ_PRODUCT_QUERY_URL, token, params={"pid": pid})
            if not product_detail or not isinstance(product_detail, dict):
                product_detail = item

            nom_original = product_detail.get("productName") or item.get("nameEn") or item.get("productName") or ""
            nom_traduite = traduire_texte(nom_original)
            if not nom_traduite:
                nom_traduite = nom_original

            img_raw = product_detail.get("productImage") or item.get("bigImage") or item.get("productImage") or ""
            img_clean = nettoyer_texte(img_raw)
            if img_clean.startswith("["):
                try:
                    img_list = json.loads(img_clean)
                    img_clean = img_list[0] if img_list else ""
                except Exception:
                    pass
            images = [img_clean] if img_clean else []

            poids_reel = safe_float(product_detail.get("productWeight", item.get("productWeight", 0.0)))
            product_fee = safe_float(product_detail.get("productFee", item.get("productFee", 0.0)))

            tailles = []
            couleurs = []
            prix_variants = []
            details_list = []
            final_parent_sku = ""
            shipping_cost_us = 0.0
            shipping_cost_base = 0.0
            total_inventory = 0

            variants = product_detail.get("variants", []) or [item]
            
            for var in variants:
                if not isinstance(var, dict):
                    continue
                
                vid = var.get("vid") or var.get("variantId")
                if vid:
                    vid_data = api_get(CJ_PRODUCT_VARIANT_URL, token, params={"vid": vid})
                    if vid_data and isinstance(vid_data, dict):
                        var.update(vid_data)

                raw_sku = var.get("variantSku") or var.get("sku") or item.get("sku") or ""
                if raw_sku:
                    sku_var = str(raw_sku).strip().upper()
                    if not final_parent_sku:
                        final_parent_sku = sku_var
                else:
                    sku_var = "N/A"

                size = var.get("variantSize") or var.get("size")
                color = var.get("variantColor") or var.get("color")
                inventory = int(var.get("inventory") or var.get("stock") or 0)
                total_inventory += inventory

                if size and str(size) not in tailles:
                    tailles.append(str(size))
                if color and str(color) not in couleurs:
                    couleurs.append(str(color))

                price_var = safe_float(var.get("variantPrice") or var.get("sellPrice") or item.get("sellPrice", 0))
                if price_var > 0 and price_var not in prix_variants:
                    prix_variants.append(price_var)

                if vid and poids_reel > 0:
                    shipping_cost_us = calculate_logistics(token, vid, poids_reel, ship_to="US")
                    shipping_cost_base = calculate_logistics(token, vid, poids_reel, ship_to="FR")

                details_list.append(f"SKU: {sku_var} | Couleur: {color or 'N/A'} | Taille: {size or 'N/A'} | Prix: {price_var}€ | Stock: {inventory}")

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
                "shippingUS": round(shipping_cost_us, 2),
                "stock": total_inventory
            }
            formatted_products.append(product_obj)
            print(f"   ✅ Produit ajouté avec succès ! (SKU: {final_parent_sku} | Stock total: {total_inventory})")

        except Exception as err:
            continue

    with open("update_stock.json", "w", encoding="utf-8") as f:
        json.dump(formatted_products, f, ensure_ascii=False, indent=4)
    print(f"🎉 Succès : {len(formatted_products)} produits mis à jour dans update_stock.json")

if __name__ == "__main__":
    generate_update_stock_json()
