from collections import defaultdict
import os
import json
import requests
from deep_translator import GoogleTranslator

# Clé API CJ (récupérée depuis les secrets GitHub)
CJ_API_KEY = os.environ.get("CJ_API_KEY")
MOTS_CLES_RECHERCHE = ["Lady Dress", "Women Dress", "Women clothing"]

CJ_AUTH_URL = "https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken"
CJ_PRODUCT_LIST_V2_URL = "https://developers.cjdropshipping.com/api2.0/v1/product/listV2"
CJ_VARIANT_QUERY_URL = "https://developers.cjdropshipping.com/api2.0/v1/product/variant/query"
CJ_FREIGHT_URL = "https://developers.cjdropshipping.com/api2.0/v1/logistic/freightCalculate"

def get_cj_access_token():
    headers = {"Content-Type": "application/json"}
    if not CJ_API_KEY:
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
    except Exception:
        pass
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

def get_product_variants(token, pid):
    headers = {
        "CJ-Access-Token": token,
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(CJ_VARIANT_QUERY_URL, headers=headers, params={"pid": pid}, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and data.get("result"):
                return data.get("data")
    except Exception:
        pass
    return None

def get_logistics_details_for_country(token, vid, weight, ship_to="US"):
    headers = {
        "CJ-Access-Token": token,
        "Content-Type": "application/json"
    }
    
    if weight <= 0 or not vid:
        return "N/A", 0.0

    payload = {
        "startCountryCode": "CN",
        "endCountryCode": ship_to,
        "products": [
            {
                "vid": vid,
                "quantity": 1,
                "weight": weight
            }
        ]
    }
    try:
        res = requests.post(CJ_FREIGHT_URL, json=payload, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data.get("result") and data.get("data"):
                logistic_list = data.get("data")
                if isinstance(logistic_list, list) and len(logistic_list) > 0:
                    first_logistic = logistic_list[0]
                    method_name = first_logistic.get("logisticName", "Standard Shipping")
                    price = float(first_logistic.get("logisticPrice", 0.0))
                    return method_name, price
    except Exception:
        pass
    return "N/A", 0.0

def safe_float(val, default=0.0):
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    
    val_str = str(val).strip()
    if not val_str or val_str.lower() == "nan":
        return default
        
    if "--" in val_str:
        val_str = val_str.split("--")[0].strip()
    elif "-" in val_str and not val_str.startswith("-"):
        val_str = val_str.split("-")[0].strip()
        
    try:
        return float(val_str)
    except ValueError:
        pass
        
    import re
    matches = re.findall(r"[-+]?\d*\.\d+|\d+", val_str)
    if matches:
        try:
            return float(matches[0])
        except ValueError:
            pass
            
    return default

def nettoyer_texte(val):
    if not val:
        return ""
    if isinstance(val, list):
        val = val[0] if val else ""
    val_str = str(val).strip()
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

def generate_update_stock_json():
    token = get_cj_access_token()
    if not token:
        with open("update_stock.json", "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)
        return

    all_items_dict = {} 
    
    for keyword in MOTS_CLES_RECHERCHE:
        print(f"🔍 Recherche active avec le mot-clé : '{keyword}'")
        
        for page_num in range(1, 4):
            params = {
                "page": page_num,
                "size": 100,
                "keyWord": keyword,
                "features": "enable_description"
            }
            
            raw_response = api_get(CJ_PRODUCT_LIST_V2_URL, token, params=params)
            
            if raw_response and isinstance(raw_response, dict):
                content_data = raw_response.get("content")
                temp_list = []
                if isinstance(content_data, dict):
                    temp_list = content_data.get("productList", [])
                elif isinstance(content_data, list):
                    temp_list = content_data

                if temp_list:
                    print(f"   📄 Page {page_num} : {len(temp_list)} produits récupérés pour '{keyword}'.")
                    for item in temp_list:
                        if isinstance(item, dict):
                            actual_product = item.get("productList")
                            if isinstance(actual_product, dict):
                                item_data = actual_product
                            elif isinstance(actual_product, list) and len(actual_product) > 0 and isinstance(actual_product[0], dict):
                                item_data = actual_product[0]
                            else:
                                item_data = item
                            
                            pid = item_data.get("pid") or item_data.get("id") or item_data.get("productId") or item_data.get("goodsId")
                            if pid:
                                all_items_dict[pid] = item_data
                else:
                    break

    products_to_process = list(all_items_dict.values())

    if not products_to_process:
        with open("update_stock.json", "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)
        print("🎉 Succès global : 0 produits enregistrés dans update_stock.json")
        return

    print(f"📦 Total de produits uniques à traiter : {len(products_to_process)}")
    
    produits_figures = {}
    
    for index, item_data in enumerate(products_to_process, start=1):
        try:
            pid = item_data.get("pid") or item_data.get("id") or item_data.get("productId") or item_data.get("goodsId")
            if not pid:
                continue

            nom_original = item_data.get("productName") or item_data.get("nameEn") or item_data.get("name") or "Produit sans nom"
            nom_traduite = traduire_texte(nom_original)
            if not nom_traduite:
                nom_traduite = nom_original

            img_raw = item_data.get("productImage") or item_data.get("bigImage") or item_data.get("image") or ""
            img_clean = nettoyer_texte(img_raw)
            images = [img_clean] if img_clean else []

            product_fee = safe_float(item_data.get("productFee"))
            price_base = safe_float(item_data.get("sellPrice"))

            variants = get_product_variants(token, pid)
            if not variants or not isinstance(variants, list):
                variants = item_data.get("variants", []) or item_data.get("variantList", [])
            if not variants:
                variants = [item_data]

            liste_variantes_produit = []

            for var in variants:
                if not isinstance(var, dict):
                    continue
                
                vid = var.get("vid") or var.get("variantId") or var.get("id")
                
                # Récupération élargie du poids avec secours par défaut (100.0g)
                poids_var = safe_float(
                    var.get("variantWeight") or 
                    var.get("weight") or 
                    var.get("packWeight") or 
                    var.get("gram") or 
                    var.get("productWeight") or
                    item_data.get("productWeight") or
                    item_data.get("weight") or 
                    100.0
                )

                raw_sku = var.get("variantSku") or var.get("sku") or item_data.get("sku") or ""
                sku_var = str(raw_sku).strip().upper() if raw_sku else str(item_data.get("spu") or pid).upper()

                # Extraction robuste de la taille et de la couleur
                variant_name_str = str(var.get("variantName") or "")
                
                size = (
                    var.get("variantSize") or 
                    var.get("size") or 
                    (variant_name_str.split("/")[-1].strip() if "/" in variant_name_str else "N/A")
                )
                
                color = (
                    var.get("variantColor") or 
                    var.get("color") or 
                    (variant_name_str.split("/")[0].strip() if "/" in variant_name_str else "N/A")
                )

                inventory = int(safe_float(var.get("inventory") or var.get("stock") or var.get("totalInventory")))
                price_var = safe_float(var.get("variantPrice") or var.get("sellPrice") or price_base)

                # Calcul logistique indépendant (FR & US)
                m_fr, c_fr = "N/A", 0.0
                m_us, c_us = "N/A", 0.0
                
                if vid and poids_var > 0:
                    m_fr, c_fr = get_logistics_details_for_country(token, vid, poids_var, ship_to="FR")
                    m_us, c_us = get_logistics_details_for_country(token, vid, poids_var, ship_to="US")

                variant_obj = {
                    "sku": sku_var,
                    "vid": vid,
                    "taille": str(size),
                    "couleur": str(color),
                    "prix": round(price_var, 2),
                    "poids": poids_var,
                    "stock": inventory,
                    "shippingMethodFR": m_fr,
                    "shippingCostFR": round(c_fr, 2),
                    "shippingMethodUS": m_us,
                    "shippingCostUS": round(c_us, 2)
                }
                
                if variant_obj not in liste_variantes_produit:
                    liste_variantes_produit.append(variant_obj)

            produit_unique = {
                "dropshipping": "CJ Dropshipping",
                "pid": pid,
                "nom": nom_traduite,
                "prixBase": round(price_base, 2),
                "productFee": round(product_fee, 2),
                "images": images,
                "variantes": liste_variantes_produit
            }

            produits_figures[pid] = produit_unique
            print(f"   ✅ [{index}/{len(products_to_process)}] Traité : {nom_traduite[:30]}... ({len(liste_variantes_produit)} variantes regroupées)")

        except Exception as err:
            print(f"   ⚠️ Erreur sur le produit {index}: {err}")
            continue

    resultat_final = list(produits_figures.values())

    with open("update_stock.json", "w", encoding="utf-8") as f:
        json.dump(resultat_final, f, ensure_ascii=False, indent=4)
        
    print(f"🎉 Succès global : {len(resultat_final)} produits uniques enregistrés dans update_stock.json")

if __name__ == "__main__":
    generate_update_stock_json()
