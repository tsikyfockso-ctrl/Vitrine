import os
import json
import requests
import time
import hashlib
from deep_translator import GoogleTranslator

APP_KEY = os.environ.get("ALIBABA_APP_KEY", "504452")
APP_SECRET = os.environ.get("ALIBABA_APP_SECRET", "yJ6EZQfA529GJbpDxKqqoP61ww30JH0R")

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
    """
    Récupère un jeton d'accès OAuth auprès de la passerelle Alibaba Open Platform.
    """
    timestamp = str(int(time.time() * 1000))
    payload = {
        "app_key": APP_KEY,
        "timestamp": timestamp,
        "format": "json",
        "v": "2.0",
        "sign_method": "md5",
        "method": "auth.token.create" # Point de terminaison d'authentification OAuth
    }
    payload["sign"] = generer_signature(payload, APP_SECRET)
    url = "https://api.alibaba.com/router/json"
    
    try:
        response = requests.post(url, data=payload, timeout=15)
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
    except Exception as e:
        print(f"⚠️ Erreur lors de la récupération du token : {e}")
    return None

def recuperer_produits_alibaba_api(keyword, access_token):
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
    url_requete = "https://api.alibaba.com/router/json"

    try:
        response = requests.post(url_requete, data=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            try:
                data = response.json()
            except Exception:
                return []
                
            if "error_response" in data:
                print(f"⚠️ Erreur API Alibaba pour '{keyword}' : {data['error_response']}")
                return []
                
            return data.get("result", {}).get("products", [])
    except Exception as e:
        print(f"⚠️ Erreur de connexion : {e}")
    
    return []

def generate_update_stock_alibaba_json():
    print("🔑 Authentification auprès d'Alibaba Open Platform...")
    access_token = obtenir_access_token()
    
    if not access_token:
        print("⚠️ Impossible d'obtenir l'access_token. Utilisation du flux CJ Dropshipping existant en secours.")
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
        except Exception:
            pass

    tous_les_produits = produits_existants.copy()
    produits_trouves = 0

    for keyword in MOTS_CLES_RECHERCHE:
        print(f"🔍 Recherche Alibaba ICBU pour : '{keyword}'")
        items = recuperer_produits_alibaba_api(keyword, access_token)
        
        for item in items:
            pid = str(item.get("productId") or item.get("id"))
            if not pid:
                continue
                
            produits_trouves += 1
            nom_original = item.get("subject") or item.get("title") or "Produit Alibaba"
            nom_fr = traduire_texte(nom_original)
            image_url = item.get("imageUrl") or item.get("image") or ""
            prix_base = float(item.get("price") or item.get("salePrice") or 10.0)
            
            tous_les_produits[pid] = {
                "dropshipping": "Alibaba",
                "pid": pid,
                "nom": nom_fr,
                "prixBase": round(prix_base, 2),
                "images": [image_url] if image_url else [],
                "variantes": [{
                    "sku": pid,
                    "vid": pid,
                    "taille": "Standard",
                    "couleur": "Unique",
                    "prix": prix_base,
                    "poids": 0.5,
                    * "stock": 100,
                    "shippingMethodFR": "Alibaba Standard",
                    "shippingCostFR": 0.0,
                    "shippingMethodUS": "Alibaba Standard",
                    "shippingCostUS": 0.0
                }]
            }

    resultat_final = list(tous_les_produits.values())
    with open("update_alibaba_stock.json", "w", encoding="utf-8") as f:
        json.dump(resultat_final, f, ensure_ascii=False, indent=4)
        
    print(f"🎉 Synchronisation terminée : {len(resultat_final)} produits enregistrés.")

if __name__ == "__main__":
    generate_update_stock_alibaba_json()
