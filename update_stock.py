import os
import json
import requests
from deep_translator import GoogleTranslator

# Clé API CJ (récupérée depuis les secrets GitHub)
CJ_API_KEY = os.environ.get("CJ_API_KEY")
MOTS_CLES_RECHERCHE = ["Lady Dress", "Women Dress", "Dress","Women Clothing"]

CJ_AUTH_URL = "https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken"
CJ_PRODUCT_LIST_V2_URL = "https://developers.cjdropshipping.com/api2.0/v1/product/listV2"
CJ_PRODUCT_DETAILS_URL = "https://developers.cjdropshipping.com/api2.0/v1/product/details"
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

def get_product_details(token, pid):
    """Interroge le module officiel Product Details pour récupérer stock, poids et variantes exacts"""
    headers = {
        "CJ-Access-Token": token,
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(CJ_PRODUCT_DETAILS_URL, headers=headers, params={"pid": pid}, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and data.get("result"):
                return data.get("data")
    except Exception:
        pass
    return None

def calculate_logistics_for_country(token, vid, weight, ship_to="US"):
    headers = {
        "CJ-Access-Token": token,
        "Content-Type": "application/json"
    }
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
                    return float(logistic_list[0].get("logisticPrice", 0.0))
    except Exception:
        pass
        
    return 0.0

def nettoyer_texte(val):
    if not val:
        return ""
    if isinstance(val, list):
        val = val[0] if val else ""
    val_str = str(val).strip()
    return val_str.strip('[]"\'')

def traduire_texte(texte):
    texte_propre = nettoyer_texte(texte)
    if not texte_propre or "Error 500" in texte_propre:
        return ""
    try:
        trads = GoogleTranslator(source='auto', target='fr').translate(texte_propre)
        resultat = nettoyer_texte(trads)
        if "Error 500" in resultat or "Server Error" in resultat:
            return texte_propre
        return resultat
    except Exception:
        return texte_propre

def generate_update_stock_json():
    token = get_cj_access_token()
    if not token:
        with open("update_stock.json", "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)
        return

    all_pids = set()
    
    # Étape 1 : Récupération des PIDs via la recherche par mot-clé
    for keyword in MOTS_CLES_RECHERCHE:
        print(f"🔍 Recherche active avec le mot-clé : '{keyword}'")
        for page_num in range(1, 3): # Limité à 2 pages pour éviter les timeouts
            params = {
                "page": page_num,
                "size": 50,
                "keyWord": keyword
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
                    for item in temp_list:
                        if isinstance(item, dict):
                            actual_product = item.get("productList") or item
                            if isinstance(actual_product, dict):
                                pid = actual_product.get("pid") or actual_product.get("id") or actual_product.get("productId")
                                if pid:
                                    all_pids.add(pid)
                else:
                    break

    pids_list = list(all_pids)
    if not pids_list:
        with open("update_stock.json", "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)
        print("🎉 Succès global : 0 produits trouvés.")
        return

    print(f"📦 Total de produits uniques à analyser en détail : {len(pids_list)}")
    formatted_products = []
    
    # Étape 2 : Appel du module de détails pour chaque produit
    for index, pid in enumerate(pids_list, start=1):
        try:
            item_data = get_product_details(token, pid)
            if not item_data:
                continue

            nom_original = item_data.get("productName") or item_data.get("nameEn") or item_data.get("name") or "Produit sans nom"
            nom_traduite = traduire_texte(nom_original)
            if not nom_traduite or "Error 500" in nom_traduite:
                nom_traduite = nom_original

            img_raw = item_data.get("productImage") or item_data.get("bigImage") or item_data.get("image") or ""
            images = [nettoyer_texte(img_raw)] if img_raw else []

            poids_reel = float(item_data.get("productWeight") or item_data.get("weight") or 0.0)
            product_fee = float(item_data.get("productFee") or 0.0)

            tailles = []
            couleurs = []
            prix_variants = []
            details_list = []
            total_inventory = 0
            first_variant_sku = ""
            first_vid = ""
            shipping_costs = {"FR": 0.0, "US": 0.0}

            variants = item_data.get("variants", []) or item_data.get("variantList", []) or item_data.get("skuList", [])
            if not variants:
                variants = [item_data]

            for var in variants:
                if not isinstance(var, dict):
                    continue
                
                vid = var.get("vid") or var.get("variantId") or var.get("id")
                if not first_vid and vid:
                    first_vid = vid

                raw_sku = var.get("variantSku") or var.get("sku") or item_data.get("sku") or ""
                sku_var = str(raw_sku).strip().upper() if raw_sku else "N/A"
                
                if not first_variant_sku and sku_var != "N/A":
                    first_variant_sku = sku_var

                size = var.get("variantSize") or var.get("size")
                color = var.get("variantColor") or var.get("color")
                inventory = int(var.get("inventory") or var.get("stock") or var.get("totalInventory") or 0)
                total_inventory += inventory

                if size and str(size) not in tailles:
                    tailles.append(str(size))
                if color and str(color) not in couleurs:
                    couleurs.append(str(color))

                price_var = float(var.get("variantPrice") or var.get("sellPrice") or item_data.get("sellPrice") or 0)
                if price_var > 0 and price_var not in prix_variants:
                    prix_variants.append(price_var)

                details_list.append(f"SKU: {sku_var} | Couleur: {color or 'N/A'} | Taille: {size or 'N/A'} | Prix: {price_var}€ | Stock: {inventory}")

            if poids_reel == 0.0:
                for var in variants:
                    p_var = float(var.get("variantWeight") or var.get("weight") or 0.0)
                    if p_var > 0:
                        poids_reel = p_var
                        break

            # Calcul des frais de port automatisés via le premier VID valide trouvé
            if first_vid and poids_reel > 0:
                shipping_costs["FR"] = calculate_logistics_for_country(token, first_vid, poids_reel, ship_to="FR")
                shipping_costs["US"] = calculate_logistics_for_country(token, first_vid, poids_reel, ship_to="US")

            final_product_sku = first_variant_sku if first_variant_sku else (item_data.get("spu") or pid)

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
                "shippingCostFR": round(shipping_costs.get("FR", 0.0), 2),
                "shippingCostUS": round(shipping_costs.get("US", 0.0), 2),
                "stock": total_inventory
            }
            formatted_products.append(product_obj)
            print(f"   ✅ [{index}/{len(pids_list)}] Traité : {nom_traduite[:30]}... (Stock: {total_inventory} | Poids: {poids_reel}g | FR: {shipping_costs['FR']}€)")

        except Exception as err:
            print(f"   ⚠️ Erreur sur le produit {index}: {err}")
            continue

    with open("update_stock.json", "w", encoding="utf-8") as f:
        json.dump(formatted_products, f, ensure_ascii=False, indent=4)
    print(f"🎉 Succès global : {len(formatted_products)} produits enregistrés dans update_stock.json")

if __name__ == "__main__":
    generate_update_stock_json()
