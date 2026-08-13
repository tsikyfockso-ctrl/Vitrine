import os
import json
import requests
from deep_translator import GoogleTranslator

# Clé API CJ (récupérée depuis les secrets GitHub)
CJ_API_KEY = os.environ.get("CJ_API_KEY")

# Mots-clés de recherche (navigation humaine par synonymes)
MOTS_CLES_RECHERCHE = ["Lady Dress", "Women Dress", "Dress"]

# URL officielle de l'API CJ V2.0 (ListV2)
CJ_AUTH_URL = "https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken"
CJ_PRODUCT_LIST_V2_URL = "https://developers.cjdropshipping.com/api2.0/v1/product/listV2"
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

def calculate_logistics(token, vid, weight, ship_to="US" or "FR"):
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
    token = get_cj_access_token()
    if not token:
        print("❌ Impossible d'obtenir le token d'accès.")
        with open("update_stock.json", "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)
        return

    items = []
    
    # 🧠 Comportement humain : Recherche intelligente par mots-clés successifs
    for keyword in MOTS_CLES_RECHERCHE:
        print(f"🧠 [Comportement Humain] Recherche listV2 avec le mot-clé : '{keyword}'")
        
        # Paramètres exacts conformes à la documentation de la capture d'écran
        params = {
            "page": 1,
            "size": 20,
            "keyWord": keyword,
            "features": "enable_description"
        }
        
        raw_response = api_get(CJ_PRODUCT_LIST_V2_URL, token, params=params)

        temp_items = []
        if raw_response:
            if isinstance(raw_response, dict):
                # Analyse des différentes structures paginées renvoyées par l'API V2
                temp_items = (
                    raw_response.get("list") or 
                    raw_response.get("productList") or 
                    raw_response.get("content") or 
                    raw_response.get("records") or []
                )
            elif isinstance(raw_response, list):
                temp_items = raw_response

        if temp_items:
            items = temp_items
            print(f"✅ Trouvé ! {len(items)} produits récupérés avec succès.")
            break
        else:
            print(f"⚠️ Aucun résultat pour '{keyword}', essai d'un autre terme...")

    if not items:
        print("❌ Aucun produit trouvé malgré l'élargissement de la recherche.")
        with open("update_stock.json", "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)
        return

    print(f"👁️ Analyse et traitement direct de {len(items)} produits...")
    formatted_products = []

    for index, item in enumerate(items, start=1):
        try:
            if not isinstance(item, dict):
                continue
            
            # Extraction directe des identifiants depuis l'objet listV2
            pid = item.get("pid") or item.get("id") or item.get("productId") or item.get("goodsId")
            if not pid:
                continue

            nom_original = item.get("productName") or item.get("nameEn") or item.get("name") or "Produit sans nom"
            nom_traduite = traduire_texte(nom_original)
            if not nom_traduite:
                nom_traduite = nom_original

            img_raw = item.get("productImage") or item.get("bigImage") or item.get("image") or ""
            img_clean = nettoyer_texte(img_raw)
            if img_clean.startswith("["):
                try:
                    img_list = json.loads(img_clean)
                    img_clean = img_list[0] if img_list else ""
                except Exception:
                    pass
            images = [img_clean] if img_clean else []

            poids_reel = safe_float(item.get("productWeight", 0.0))
            product_fee = safe_float(item.get("productFee", 0.0))

            tailles = []
            couleurs = []
            prix_variants = []
            details_list = []
            shipping_cost = 0.0
            total_inventory = 0
            first_variant_sku = ""

            variants = item.get("variants", []) or item.get("variantList", [])
            if not variants:
                variants = [item] # Fallback si le produit est simple
            
            for var in variants:
                if not isinstance(var, dict):
                    continue
                
                vid = var.get("vid") or var.get("variantId")
                raw_sku = var.get("variantSku") or var.get("sku") or item.get("sku") or ""
                sku_var = str(raw_sku).strip().upper() if raw_sku else "N/A"
                
                if not first_variant_sku and sku_var != "N/A":
                    first_variant_sku = sku_var

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
                    shipping_cost = calculate_logistics(token, vid, poids_reel, ship_to="US")

                details_list.append(f"SKU: {sku_var} | Couleur: {color or 'N/A'} | Taille: {size or 'N/A'} | Prix: {price_var}€ | Stock: {inventory}")

            final_product_sku = first_variant_sku if first_variant_sku else (item.get("spu") or pid)

            product_obj = {
                "dropshipping": "CJ Dropshipping",
                "sku": str(final_product_sku).upper(),
                "nom": nom_traduite,
                "tailles": tailles,
                "couleurs": couleurs,
                "prix": prix_variants,
                "images": images,
                "details": " | ".join(filter(None, details_list)),
                "poids": poids_reel,
                "productFee": round(product_fee, 2),
                "shippingCost": round(shipping_cost, 2),
                "stock": total_inventory
            }
            formatted_products.append(product_obj)
            print(f"      ✅ Produit enregistré : {nom_traduite[:30]}... (Stock: {total_inventory})")

        except Exception as err:
            print(f"      ⚠️ Erreur sur un produit : {err}")
            continue

    with open("update_stock.json", "w", encoding="utf-8") as f:
        json.dump(formatted_products, f, ensure_ascii=False, indent=4)
    print(f"🎉 Succès global : {len(formatted_products)} produits analysés et enregistrés dans update_stock.json")

if __name__ == "__main__":
    generate_update_stock_json()
