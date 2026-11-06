import os
import json
import requests
import time
import hashlib
from deep_translator import GoogleTranslator

APP_KEY = os.environ.get("ALIBABA_APP_KEY", "505288")
APP_SECRET = os.environ.get("ALIBABA_APP_SECRET", "B2FvDgenPgnGwvdSS0z2YKxPxeKBXrSj")

MOTS_CLES_RECHERCHE = ["Women Dress", "Lady Dress", "Women clothing"]

def generer_signature(params, secret):
    sorted_params = sorted(params.items())
    query_string = "".join([f"{k}{v}" for k, v in sorted_params])
    sign_str = secret + query_string + secret
    return hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()

def traduire_texte(texte):
    if not texte:
        return "Nom indisponible"
    try:
        trads = GoogleTranslator(source='auto', target='fr').translate(str(texte).strip())
        return trads if trads else texte
    except Exception:
        return texte

def obtenir_access_token():
    timestamp = str(int(time.time() * 1000))
    payload = {
        "app_key": APP_KEY,
        "timestamp": timestamp,
        "format": "json",
        "v": "2.0",
        "sign_method": "md5",
        "method": "auth.token.create"
    }
    payload["sign"] = generer_signature(payload, APP_SECRET)
    
    # URL de passerelle officielle OpenAPI corrigée
    url = "https://gw.open.alibaba.com/openapi/json"
    
    try:
        response = requests.post(url, data=payload, timeout=15)
        print(f"🔍 Réponse brute Alibaba (Auth) [Statut {response.status_code}] : {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                return token
            else:
                print(f"⚠️ JSON reçu mais pas d'access_token : {data}")
    except Exception as e:
        print(f"⚠️ Erreur de connexion pour le token : {e}")
    return None

def recuperer_details_produit_reel(product_id, access_token):
    timestamp = str(int(time.time() * 1000))
    payload = {
        "app_key": APP_KEY,
        "timestamp": timestamp,
        "format": "json",
        "v": "2.0",
        "sign_method": "md5",
        "method": "alibaba.icbu.product.get",
        "product_id": product_id,
        "access_token": access_token
    }
    
    payload["sign"] = generer_signature(payload, APP_SECRET)
    headers = {"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"}
    
    # URL de passerelle officielle OpenAPI corrigée
    url_requete = "https://gw.open.alibaba.com/openapi/json"

    try:
        response = requests.post(url_requete, data=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if "error_response" in data:
                return None
            return data.get("result", data.get("product_info", {}))
    except Exception as e:
        print(f"⚠️ Erreur de connexion pour le produit {product_id} : {e}")
    
    return None

def rechercher_produits_alibaba(keyword, access_token):
    timestamp = str(int(time.time() * 1000))
    payload = {
        "app_key": APP_KEY,
        "timestamp": timestamp,
        "format": "json",
        "v": "2.0",
        "sign_method": "md5",
        "method": "alibaba.icbu.product.searchV2",
        "keywords": keyword,
        "page_size": 20,
        "page_no": 1,
        "access_token": access_token
    }
    
    payload["sign"] = generer_signature(payload, APP_SECRET)
    headers = {"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"}
    
    # URL de passerelle officielle OpenAPI corrigée
    url_requete = "https://gw.open.alibaba.com/openapi/json"

    try:
        response = requests.post(url_requete, data=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if "error_response" in data:
                print(f"⚠️ Erreur API Alibaba pour '{keyword}' : {data['error_response']}")
                return []
            return data.get("result", {}).get("products", [])
    except Exception as e:
        print(f"⚠️ Erreur de recherche : {e}")
    
    return []

def generate_update_stock_alibaba_json():
    print("🔑 Authentification auprès d'Alibaba Open Platform...")
    access_token = obtenir_access_token()
    
    if not access_token:
        print("⚠️ Impossible d'obtenir l'access_token. Regardez le message brut ci-dessus pour identifier le paramètre manquant.")
        return

    produits_existants = {}
    if os.path.exists("update_alibaba_stock.json"):
        try:
            with open("update_alibaba_stock.json", "r", encoding="utf-8") as f:
                old_data = json.load(f)
                if isinstance(old_data, list):
                    for p in old_data:
                        pid = p.get("pid")
                        if pid:
                            produits_existants[pid] = p
        except Exception as e:
            print(f"⚠️ Impossible de lire l'ancien fichier JSON : {e}")

    tous_les_produits = produits_existants.copy()
    produits_trouves = 0

    for keyword in MOTS_CLES_RECHERCHE:
        print(f"🔍 Recherche Alibaba ICBU pour le mot-clé : '{keyword}'")
        items = rechercher_produits_alibaba(keyword, access_token)
        
        for item in items:
            pid = str(item.get("productId") or item.get("id"))
            if not pid:
                continue
            
            print(f"📥 Récupération des détails réels pour le produit ID: {pid}")
            details_complets = recuperer_details_produit_reel(pid, access_token)
            
            if not details_complets:
                details_complets = item

            produits_trouves += 1
            nom_original = details_complets.get("subject") or details_complets.get("title") or "Produit Alibaba"
            nom_fr = traduire_texte(nom_original)
            
            images = details_complets.get("images") or details_complets.get("imageUrlList") or [details_complets.get("imageUrl", "")]
            images = [img for img in images if img]

            prix_base = float(details_complets.get("price") or details_complets.get("salePrice") or 0.0)
            
            variantes = []
            skus_api = details_complets.get("skuList") or details_complets.get("skus", [])
            
            if skus_api:
                for sku in skus_api:
                    variantes.append({
                        "sku": str(sku.get("skuId") or pid),
                        "vid": str(sku.get("skuId") or "1"),
                        "taille": str(sku.get("size") or sku.get("specification", {}).get("size", "Standard")),
                        "couleur": str(sku.get("color") or sku.get("specification", {}).get("color", "Unique")),
                        "prix": float(sku.get("price") or prix_base),
                        "poids": float(sku.get("weight", 0.5)),
                        "stock": int(sku.get("stock") or sku.get("availableStock", 100)),
                        "shippingMethodFR": "Alibaba Standard Shipping",
                        "shippingCostFR": 0.0,
                        "shippingMethodUS": "Alibaba Standard Shipping",
                        "shippingCostUS": 0.0
                    })
            else:
                variantes.append({
                    "sku": pid,
                    "vid": pid,
                    "taille": "Standard",
                    "couleur": "Unique",
                    "prix": prix_base,
                    "poids": 0.5,
                    "stock": int(details_complets.get("stock", 100)),
                    "shippingMethodFR": "Alibaba Standard Shipping",
                    "shippingCostFR": 0.0,
                    "shippingMethodUS": "Alibaba Standard Shipping",
                    "shippingCostUS": 0.0
                })

            tous_les_produits[pid] = {
                "dropshipping": "Alibaba",
                "pid": pid,
                "nom": nom_fr,
                "prixBase": round(prix_base, 2),
                "images": images,
                "variantes": variantes
            }

    resultat_final = list(tous_les_produits.values())

    with open("update_alibaba_stock.json", "w", encoding="utf-8") as f:
        json.dump(resultat_final, f, ensure_ascii=False, indent=4)
        
    print(f"🎉 Synchronisation terminée : {len(resultat_final)} produits enregistrés dans update_alibaba_stock.json (Nouveaux: {produits_trouves})")

if __name__ == "__main__":
    generate_update_stock_alibaba_json()
