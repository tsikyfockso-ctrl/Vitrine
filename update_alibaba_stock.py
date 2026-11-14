import os
import json
import requests
import time
import hashlib
from deep_translator import GoogleTranslator

APP_KEY = os.environ.get("ALIBABA_APP_KEY", "504452")
APP_SECRET = os.environ.get("ALIBABA_APP_SECRET", "yJ6EZQfA529GJbpDxKqqoP61ww30JH0R")
ACCESS_TOKEN = os.environ.get("ALIBABA_ACCESS_TOKEN", "50000901d06tgOXdDP1329d674AMz1DHfQpwGwTkFz9QQFwO3Tqr22jvcljMlz")

MOTS_CLES_RECHERCHE = ["Women Dress", "Lady Dress", "Women clothing"]

def generer_signature_sha256(params, secret):
    # Tri alphabétique des paramètres
    sorted_params = sorted(params.items())
    query_string = "".join([f"{k}{v}" for k, v in sorted_params])
    # Signature SHA-256 spécifique à l'API REST d'Alibaba
    sign_str = secret + query_string + secret
    return hashlib.sha256(sign_str.encode('utf-8')).hexdigest().upper()

def traduire_texte(texte):
    if not texte:
        return "Nom indisponible"
    try:
        trads = GoogleTranslator(source='auto', target='fr').translate(str(texte).strip())
        return trads if trads else texte
    except Exception:
        return texte

def executer_requete_alibaba(api_path, extra_params=None):
    timestamp = str(int(time.time() * 1000))
    payload = {
        "app_key": APP_KEY,
        "timestamp": timestamp,
        "format": "json",
        "v": "2.0",
        "sign_method": "sha256",
        "access_token": ACCESS_TOKEN
    }
    
    if extra_params:
        payload.update(extra_params)
        
    payload["sign"] = generer_signature_sha256(payload, APP_SECRET)
    
    url = f"https://openapi-api.alibaba.com/rest{api_path}"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
    }

    try:
        response = requests.get(url, params=payload, headers=headers, timeout=20)
        print(f"🔍 Requête {api_path} [Statut {response.status_code}] : {response.text[:300]}")
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"⚠️ Erreur réseau pour {api_path} : {e}")
        
    return None

def generate_update_stock_alibaba_json():
    print("🚀 Interrogation du catalogue Alibaba avec la signature SHA-256...")

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
            print(f"⚠️ Lecture du fichier existant impossible : {e}")

    tous_les_produits = produits_existants.copy()
    produits_trouves = 0

    for keyword in MOTS_CLES_RECHERCHE:
        print(f"🔍 Recherche Alibaba pour le mot-clé : '{keyword}'")
        search_response = executer_requete_alibaba("/alibaba/icbu/product/search/v2", {
            "keywords": keyword,
            "page_size": 20,
            "page_no": 1
        })
        
        if not search_response:
            continue
            
        items = search_response.get("result", {}).get("products", search_response.get("products", []))
        
        for item in items:
            pid = str(item.get("productId") or item.get("id"))
            if not pid:
                continue
            
            produits_trouves += 1
            nom_original = item.get("subject") or item.get("title") or "Produit Alibaba"
            nom_fr = traduire_texte(nom_original)
            
            images = item.get("images") or item.get("imageUrlList") or [item.get("imageUrl", "")]
            images = [img for img in images if img]

            prix_base = float(item.get("price") or item.get("salePrice") or 0.0)
            
            tous_les_produits[pid] = {
                "dropshipping": "Alibaba",
                "pid": pid,
                "nom": nom_fr,
                "prixBase": round(prix_base, 2),
                "images": images,
                "variantes": [{
                    "sku": pid,
                    "vid": pid,
                    "taille": "Standard",
                    "couleur": "Unique",
                    "prix": prix_base,
                    "poids": 0.5,
                    "stock": int(item.get("stock", 100)),
                    "shippingMethodFR": "Alibaba Standard Shipping",
                    "shippingCostFR": 0.0,
                    "shippingMethodUS": "Alibaba Standard Shipping",
                    "shippingCostUS": 0.0
                }]
            }

    resultat_final = list(tous_les_produits.values())

    with open("update_alibaba_stock.json", "w", encoding="utf-8") as f:
        json.dump(resultat_final, f, ensure_ascii=False, indent=4)
        
    print(f"🎉 Synchronisation terminée : {len(resultat_final)} produits enregistrés dans update_alibaba_stock.json (Nouveaux: {produits_trouves})")

if __name__ == "__main__":
    generate_update_stock_alibaba_json()
