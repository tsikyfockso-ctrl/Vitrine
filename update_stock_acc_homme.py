from collections import defaultdict
import os
import json
import requests
from deep_translator import GoogleTranslator

# Clé API CJ (récupérée depuis les secrets GitHub)
CJ_API_KEY = os.environ.get("CJ_API_KEY")
MOTS_CLES_RECHERCHE = ["Men's shoes", "Men's Ties", "Men's Watches", "Men's Wallets", "Men's Belts"]

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
        response = requests.post(CJ_AUTH_URL, json=payload, headers=headers, timeout=15)
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
        response = requests.get(CJ_VARIANT_QUERY_URL, headers=headers, params={"pid": pid}, timeout=60)
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
    
    if not vid or not weight or weight <= 0:
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
        res = requests.post(CJ_FREIGHT_URL, json=payload, headers=headers, timeout=60)
        if res.status_code == 200:
            data = res.json()
            logistic_data = data.get("data")
            
            if data.get("result") and logistic_data:
                logistic_list = []
                if isinstance(logistic_data, list):
                    logistic_list = logistic_data
                elif isinstance(logistic_data, dict):
                    logistic_list = logistic_data.get("logisticList") or logistic_data.get("list") or []

                if isinstance(logistic_list, list) and len(logistic_list) > 0:
                    for logistic in logistic_list:
                        price = safe_float(logistic.get("logisticPrice") or logistic.get("price", 0.0))
                        method_name = logistic.get("logisticName") or logistic.get("name")
                        if method_name:
                            return str(method_name).strip(), round(price, 2)
                    
    except Exception as e:
        print(f"    ⚠️ Erreur logistique pour VID {vid} ({ship_to}) : {e}")
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
    
    # Si le texte reçu est une erreur serveur HTML de l'API, 
    # on évite de planter mais on ne met plus "Produit CJ" aveuglément
    if "500" in val_str or "Server Error" in val_str or "<html" in val_str.lower():
        return "" # ou un nom générique basé sur l'ID si vous préférez
        
    return val_str.strip('[]"\'')

def traduire_texte(texte):
    texte_propre = nettoyer_texte(texte)
    # Si le texte propre est vide ou invalide, on retourne une chaîne vide 
    # ou on garde le texte d'origine au lieu de forcer "Produit CJ"
    if not texte_propre:
        return "Nom indisponible" 
        
    try:
        trads = GoogleTranslator(source='auto', target='fr').translate(texte_propre)
        resultat = nettoyer_texte(trads)
        if "500" in resultat or "Server Error" in resultat:
            return texte_propre
        return resultat
    except Exception:
        return texte_propre

def generate_update_stock_acc_homme_json():
    token = get_cj_access_token()
    
    # 1. Charger l'ancien fichier JSON existant pour préserver les produits ayant encore du stock
    produits_existants = {}
    if os.path.exists("update_stock_acc_homme.json"):
        try:
            with open("update_stock_acc_homme.json", "r", encoding="utf-8") as f:
                old_data = json.load(f)
                if isinstance(old_data, list):
                    for p in old_data:
                        pid_old = p.get("pid")
                        if pid_old:
                            # On vérifie si au moins une variante a un stock > 0
                            has_stock = any(v.get("stock", 0) > 0 for v in p.get("variantes", []))
                            if has_stock:
                                produits_existants[pid_old] = p
        except Exception as e:
            print(f"    ⚠️ Impossible de lire l'ancien fichier JSON : {e}")

    if not token:
        # S'il n'y a pas de token, on conserve au moins ce qu'on a déjà en stock
        if produits_existants:
            with open("update_stock_acc_homme.json", "w", encoding="utf-8") as f:
                json.dump(list(produits_existants.values()), f, ensure_ascii=False, indent=4)
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
                    print(f"    📄 Page {page_num} : {len(temp_list)} produits récupérés pour '{keyword}'.")
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
        # Si l'API ne renvoie rien, on garde les anciens produits en stock
        resultat_final = list(produits_existants.values())
        with open("update_stock_acc_homme.json", "w", encoding="utf-8") as f:
            json.dump(resultat_final, f, ensure_ascii=False, indent=4)
        print("🎉 Succès global : Utilisation des stocks existants (aucun nouveau produit récupéré)")
        return

    print(f"📦 Total de produits uniques à traiter : {len(products_to_process)}")
    
    # On commence par inclure les anciens produits qui ont encore du stock
    produits_figures = produits_existants.copy()
    
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
            
            global_warehouse_stock = int(safe_float(
                item_data.get("warehouseInventoryNum") or 
                item_data.get("totalVerifiedInventory") or 
                item_data.get("inventory") or 0
            ))

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
                
                poids_var = safe_float(
                    var.get("variantWeight") or 
                    var.get("weight") or 
                    var.get("packWeight") or 
                    var.get("gram") or 
                    var.get("productWeight") or
                    item_data.get("productWeight") or
                    item_data.get("weight") or 
                    0.0
                )

                raw_sku = var.get("variantSku") or var.get("sku") or item_data.get("sku") or ""
                sku_var = str(raw_sku).strip().upper() if raw_sku else str(item_data.get("spu") or pid).upper()

                variant_key_str = str(var.get("variantKey") or "").strip()
                
                color = "N/A"
                size = "N/A"

                if variant_key_str and "-" in variant_key_str:
                    parts = variant_key_str.split("-")
                    color = parts[0].strip()
                    size = parts[-1].strip()
                elif variant_key_str:
                    color = variant_key_str

                inventory = int(safe_float(
                    var.get("inventory") or 
                    var.get("stock") or 
                    var.get("variantInventory") or 
                    var.get("totalInventory") or 
                    var.get("warehouseInventoryNum") or 
                    global_warehouse_stock
                ))

                price_var = safe_float(var.get("variantPrice") or var.get("sellPrice") or price_base)

                m_fr, c_fr = "N/A", 0.0
                m_us, c_us = "N/A", 0.0
                
                if vid and poids_var > 0:
                    m_fr, c_fr = get_logistics_details_for_country(token, vid, poids_var, ship_to="FR")
                    m_us, c_us = get_logistics_details_for_country(token, vid, poids_var, ship_to="US")

                # --- SÉCURITÉ ANTI-N/A ---
                # Si l'API retourne N/A pour les US, on va chercher si l'ancienne version avait une valeur valide
                if m_us == "N/A" and pid in produits_existants:
                    old_prod = produits_existants[pid]
                    for old_v in old_prod.get("variantes", []):
                        if old_v.get("vid") == vid and old_v.get("shippingMethodUS") != "N/A":
                            m_us = old_v.get("shippingMethodUS")
                            c_us = old_v.get("shippingCostUS")
                            break
                # Idem par sécurité pour la France
                if m_fr == "N/A" and pid in produits_existants:
                    old_prod = produits_existants[pid]
                    for old_v in old_prod.get("variantes", []):
                        if old_v.get("vid") == vid and old_v.get("shippingMethodFR") != "N/A":
                            m_fr = old_v.get("shippingMethodFR")
                            c_fr = old_v.get("shippingCostFR")
                            break
                # -------------------------

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

            # Harmonisation des transporteurs
            best_fr_method, best_fr_cost = "N/A", 0.0
            best_us_method, best_us_cost = "N/A", 0.0

            for v in liste_variantes_produit:
                if v["shippingMethodFR"] != "N/A":
                    best_fr_method = v["shippingMethodFR"]
                    best_fr_cost = v["shippingCostFR"]
                    break
            
            for v in liste_variantes_produit:
                if v["shippingMethodUS"] != "N/A":
                    best_us_method = v["shippingMethodUS"]
                    best_us_cost = v["shippingCostUS"]
                    break

            for v in liste_variantes_produit:
                if v["shippingMethodFR"] == "N/A" and best_fr_method != "N/A":
                    v["shippingMethodFR"] = best_fr_method
                    v["shippingCostFR"] = best_fr_cost
                if v["shippingMethodUS"] == "N/A" and best_us_method != "N/A":
                    v["shippingMethodUS"] = best_us_method
                    v["shippingCostUS"] = best_us_cost

            # Vérification si le nouveau produit a du stock
            has_stock_new = any(v.get("stock", 0) > 0 for v in liste_variantes_produit)

            produit_unique = {
                "dropshipping": "CJ Dropshipping",
                "pid": pid,
                "nom": nom_traduite,
                "prixBase": round(price_base, 2),
                "productFee": round(product_fee, 2),
                "images": images,
                "variantes": liste_variantes_produit
            }

            if has_stock_new:
                # S'il a du stock, on l'ajoute ou on met à jour
                produits_figures[pid] = produit_unique
                print(f"    ✅ [{index}/{len(products_to_process)}] Ajouté/Mis à jour (En stock) : {nom_traduite[:30]}...")
            else:
                # S'il n'a plus de stock (0), on le supprime de la liste s'il y était
                if pid in produits_figures:
                    del produits_figures[pid]
                print(f"    ❌ [{index}/{len(products_to_process)}] Écarté (Rupture de stock / 0) : {nom_traduite[:30]}...")

        except Exception as err:
            print(f"    ⚠️ Erreur sur le produit {index}: {err}")
            continue

    resultat_final = list(produits_figures.values())

    with open("update_stock_acc_homme.json", "w", encoding="utf-8") as f:
        json.dump(resultat_final, f, ensure_ascii=False, indent=4)
        
    print(f"🎉 Succès global : {len(resultat_final)} produits actifs enregistrés dans update_stock_acc_homme.json")

if __name__ == "__main__":
    generate_update_stock_acc_homme_json()
