import os
import json
import requests
import time
import hashlib
from datetime import datetime, timezone, timedelta
from deep_translator import GoogleTranslator

APP_KEY = os.environ.get("ALIBABA_APP_KEY", "505290")
APP_SECRET = os.environ.get("ALIBABA_APP_SECRET", "cPs3QbmUQ2MNPAqPIek1hRMENUtyM4pm")
ACCESS_TOKEN = os.environ.get("ALIBABA_ACCESS_TOKEN", "50000901127xfbaaykUFnQBSQGfkEvBNxxjfgxm13894bf7xdUxHjZAvp5SVn6")

MOTS_CLES_RECHERCHE = ["Women Dress", "Lady Dress", "Women clothing"]

def generer_signature_top(params, secret):
    # Tri alphabétique strict des paramètres (en excluant 'sign')
    filtered_params = {k: v for k, v in params.items() if k != "sign"}
    sorted_params = sorted(filtered_params.items())
    query_string = "".join([f"{k}{v}" for k, v in sorted_params])
    
    # Standard de signature Alibaba TOP (Secret + QueryString + Secret)
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

def executer_requete_alibaba(method_name, extra_params=None):
    # Format de timestamp requis par l'API TOP : yyyy-MM-dd HH:mm:ss (GMT+8)
    tz_gmt8 = timezone(timedelta(hours=8))
    timestamp = datetime.now(tz_gmt8).strftime('%Y-%m-%d %H:%M:%S')
    
    payload = {
        "method": method_name,
        "app_key": APP_KEY,
        "timestamp": timestamp,
        "format": "json",
        "v": "2.0",
        "sign_method": "sha256",
        "session": ACCESS_TOKEN
    }
    
    if extra_params:
        payload.update(extra_params)
        
    payload["sign"] = generer_signature_top(payload, APP_SECRET)
    
    # URL du routeur officiel Alibaba TOP
    url = "https://api.taobao.com/router/rest"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
    }

    try:
        response = requests.post(url, data=payload, headers=headers, timeout=20)
        print(f"🔍 Requête {method_name} [Statut {response.status_code}] : {response.text[:300]}")
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"⚠️ Erreur réseau pour {method_name} : {e}")
        
    return None

def generate_update_stock_alibaba_json():
    print("🚀 Interrogation du catalogue Alibaba via l'API TOP...")

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
        # Méthode standard de recherche de produits ICBU
        search_response = executer_requete_alibaba("alibaba.icbu.product.search", {
            "keywords": keyword,
            "page_size": 20,
            "page_no": 1
        })
        
        if not search_response:
            continue
            
        # Extraction des items selon la structure de réponse de l'API
        result_node = search_response.get("alibaba_icbu_product_search_response", search_response.get("result", {}))
        items = result_node.get("products", result_node.get("result_list", []))
        
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
