import os
import json
import requests
import time
import hashlib
from deep_translator import GoogleTranslator

# Récupération des clés depuis les secrets GitHub
APP_KEY = os.environ.get("ALIBABA_APP_KEY", "504452")
APP_SECRET = os.environ.get("ALIBABA_APP_SECRET", "yJ6EZQfA529GJbpDxKqqoP61ww30JH0R")

MOTS_CLES_RECHERCHE = ["Women Dress", "Lady Dress", "Women clothing"]

def generer_signature(params, secret):
    """
    Génère la signature MD5 requise par l'Open Platform Alibaba.
    """
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

def recuperer_produits_alibaba_api(keyword):
    """
    Récupère les produits via l'API Alibaba en gérant proprement les erreurs 
    pour éviter de bloquer le pipeline GitHub Actions.
    """
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
        "page_no": 1
    }
    
    payload["sign"] = generer_signature(payload, APP_SECRET)
    headers = {"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"}

    # Passerelle officielle
    url_requete = f"https://api.alibaba.com/router/json"

    try:
        response = requests.post(url_requete, data=payload, headers=headers, timeout=15)
        print(f"Requête Alibaba pour '{keyword}' - Statut : {response.status_code}")
        
        # Vérification si la réponse est bien du JSON (et non une page d'erreur HTML 404)
        if response.status_code == 200:
            try:
                data = response.json()
            except Exception:
                print(f"⚠️ La passerelle a renvoyé du HTML (API restreinte ou jeton OAuth requis).")
                return []
                
            if "error_response" in data:
                print(f"⚠️ Erreur API : {data['error_response']}")
                return []
                
            return data.get("result", {}).get("products", [])
        else:
            print(f"⚠️ Erreur HTTP {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ Erreur de connexion : {e}")
    
    return []

def generate_update_stock_alibaba_json():
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
        print(f"🔍 Recherche en cours pour : '{keyword}'")
        items = recuperer_produits_alibaba_api(keyword)
        
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
                    "stock": 100,
                    "shippingMethodFR": "Alibaba Standard",
                    "shippingCostFR": 0.0,
                    "shippingMethodUS": "Alibaba Standard",
                    "shippingCostUS": 0.0
                }]
            }

    resultat_final = list(tous_les_produits.values())

    # Sauvegarde garantie pour alimenter la vitrine Mayah Store
    with open("update_alibaba_stock.json", "w", encoding="utf-8") as f:
        json.dump(resultat_final, f, ensure_ascii=False, indent=4)
        
    print(f"🎉 Synchronisation terminée : {len(resultat_final)} produits au total dans le fichier JSON.")

if __name__ == "__main__":
    generate_update_stock_alibaba_json()
