import os
import json
import requests
from deep_translator import GoogleTranslator

CJ_API_KEY = os.environ.get("CJ_API_KEY")
MOTS_CLES_RECHERCHE = ["Lady Dress", "Women Dress"]

CJ_AUTH_URL = "https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken"
CJ_PRODUCT_LIST_V2_URL = "https://developers.cjdropshipping.com/api2.0/v1/product/listV2"

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

    all_items_dict = {} # Utilisation d'un dictionnaire avec le PID comme clé pour éviter les doublons entre les mots-clés
    
    for keyword in MOTS_CLES_RECHERCHE:
        print(f"🔍 Recherche active avec le mot-clé : '{keyword}'")
        params = {
            "page": 1,
            "size": 20, # Augmenté pour récupérer plus de résultats par mot-clé si besoin
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
                print(f"✅ {len(temp_list)} produits récupérés pour '{keyword}'.")
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

    products_to_process = list(all_items_dict.values())

    if not products_to_process:
        with open("update_stock.json", "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)
        print("🎉 Succès global : 0 produits enregistrés dans update_stock.json")
        return

    print(f"📦 Total de produits uniques à traiter : {len(products_to_process)}")
    formatted_products = []
    
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

            poids_reel = float(item_data.get("productWeight") or 0.0)
            product_fee = float(item_data.get("productFee") or 0.0)

            tailles = []
            couleurs = []
            prix_variants = []
            details_list = []
            total_inventory = 0
            first_variant_sku = ""

            variants = item_data.get("variants", []) or item_data.get("variantList", [])
            if not variants:
                variants = [item_data]

            for var in variants:
                if not isinstance(var, dict):
                    continue
                
                raw_sku = var.get("variantSku") or var.get("sku") or item_data.get("sku") or ""
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

                price_var = float(var.get("variantPrice") or var.get("sellPrice") or item_data.get("sellPrice") or 0)
                if price_var > 0 and price_var not in prix_variants:
                    prix_variants.append(price_var)

                details_list.append(f"SKU: {sku_var} | Couleur: {color or 'N/A'} | Taille: {size or 'N/A'} | Prix: {price_var}€ | Stock: {inventory}")

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
                "shippingCost": 0.0,
                "stock": total_inventory
            }
            formatted_products.append(product_obj)
            print(f"   ✅ [{index}/{len(products_to_process)}] Ajouté : {nom_traduite[:30]}... (Stock: {total_inventory})")

        except Exception as err:
            print(f"   ⚠️ Erreur sur le produit {index}: {err}")
            continue

    with open("update_stock.json", "w", encoding="utf-8") as f:
        json.dump(formatted_products, f, ensure_ascii=False, indent=4)
    print(f"🎉 Succès global : {len(formatted_products)} produits enregistrés dans update_stock.json")

if __name__ == "__main__":
    generate_update_stock_json()
