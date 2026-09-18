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
# Endpoint officiel de l'Open Platform Alibaba
ALIBABA_API_URL = "https://api.alibaba.com/router/json"

def generer_signature(params, secret):
    """
    Génère la signature MD5 requise par l'API Alibaba Open Platform.
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
    Interroge l'API Alibaba pour récupérer les produits selon un mot-clé.
    """
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
    
    payload = {
        "app_key": APP_KEY,
        "timestamp": timestamp,
        "format": "json",
        "v": "2.0",
        "sign_method": "md5",
        "method": "alibaba.icbu.product.query", # Méthode de recherche Alibaba Open Platform
        "keyword": keyword,
        "pageSize": 50,
        "pageNo": 1
    }
    
    payload["sign"] = generer_signature(payload, APP_SECRET)
    headers = {"Content-Type": "application/json;charset=utf-8"}

    try:
        response = requests.post(ALIBABA_API_URL, json=payload, headers=headers, timeout=20)
        print(f"Réponse brute Alibaba ({response.status_code}) : {response.text}")
        if response.status_code == 200:
            data = response.json()
            return data.get("result", {}).get("products", [])
    except Exception as e:
        print(f"⚠️ Erreur lors de la requête Alibaba pour '{keyword}' : {e}")
    
    return []

def generate_update_stock_alibaba_json():
    # 1. Charger l'ancien fichier JSON existant pour préserver les stocks si besoin
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

    # 2. Recherche par mots-clés
    for keyword in MOTS_CLES_RECHERCHE:
        print(f"🔍 Recherche Alibaba en cours pour : '{keyword}'")
        items = recuperer_produits_alibaba_api(keyword)
        
        for item in items:
            pid = str(item.get("productId") or item.get("id"))
            if not pid:
                continue
                
            nom_original = item.get("subject") or item.get("title") or "Produit Alibaba"
            nom_fr = traduire_texte(nom_original)
            
            image_url = item.get("imageUrl") or item.get("image") or ""
            prix_base = float(item.get("price") or item.get("salePrice") or 0.0)
            
            # Construction des variantes
            variantes = []
            variants_list = item.get("skuList", [])
            
            if variants_list:
                for var in variants_list:
                    variantes.append({
                        "sku": str(var.get("skuId") or pid),
                        "vid": str(var.get("skuId") or "1"),
                        "taille": str(var.get("size") or "Standard"),
                        "couleur": str(var.get("color") or "Unique"),
                        "prix": float(var.get("price") or prix_base),
                        "poids": float(var.get("weight") or 0.5),
                        "stock": int(var.get("stock") or 100),
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
                    "stock": int(item.get("stock") or 100),
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
                "images": [image_url] if image_url else [],
                "variantes": variantes
            }

    resultat_final = list(tous_les_produits.values())

    # 3. Sauvegarde finale au format JSON pour le site
    with open("update_alibaba_stock.json", "w", encoding="utf-8") as f:
        json.dump(resultat_final, f, ensure_ascii=False, indent=4)
        
    print(f"🎉 Succès : {len(resultat_final)} produits enregistrés dans update_stock_alibaba.json")

if __name__ == "__main__":
    generate_update_stock_alibaba_json()
