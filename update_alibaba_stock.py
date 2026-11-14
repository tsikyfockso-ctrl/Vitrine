import os
import json
import requests
import time
import hashlib
from deep_translator import GoogleTranslator

APP_KEY = os.environ.get("ALIBABA_APP_KEY", "505290")
APP_SECRET = os.environ.get("ALIBABA_APP_SECRET", "cPs3QbmUQ2MNPAqPIek1hRMENUtyM4pm")
ACCESS_TOKEN = os.environ.get("ALIBABA_ACCESS_TOKEN", "50000901127xfbaaykUFnQBSQGfkEvBNxxjfgxm13894bf7xdUxHjZAvp5SVn6")

MOTS_CLES_RECHERCHE = ["Women Dress", "Lady Dress", "Women clothing"]

def generer_signature_rest(params, secret):
    # Exclusion du paramètre 'sign' du calcul
    filtered_params = {k: v for k, v in params.items() if k != "sign"}
    
    # Tri alphabétique strict des clés
    sorted_keys = sorted(filtered_params.keys())
    
    # Concaténation clé + valeur
    query_string = "".join([f"{k}{filtered_params[k]}" for k in sorted_keys])
    
    # Standard de signature Alibaba REST API (Secret + QueryString + Secret)
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
        
    payload["sign"] = generer_signature_rest(payload, APP_SECRET)
    
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
    print("🚀 Interrogation du catalogue Alibaba (/alibaba/icbu/product/search/v2)...")

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

    api_path = "/alibaba/icbu/product/search/v2"

    for keyword in MOTS_CLES_RECHERCHE:
        print(f"🔍 Recherche Alibaba pour le mot-clé : '{keyword}'")
        search_response = executer_requete_alibaba(api_path, {
            "keywords": keyword,
            "page_size": 20,
            "page_no": 1
        })
        
        if not search_response:
            continue
            
        result_data = search_response.get("result", search_response)
        items = result_data.get("products", result_data.get("resultList", result_data.get("data", [])))
        
        for item in items:
            pid = str(item.get("productId") or item.get("id") or item.get("offerId"))
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
