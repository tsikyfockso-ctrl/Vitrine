import os
import json
import requests
import time
import hashlib
from deep_translator import GoogleTranslator

APP_KEY = os.environ.get("ALIBABA_APP_KEY", "505288")
APP_SECRET = os.environ.get("ALIBABA_APP_SECRET", "B2FvDgenPgnGwvdSS0z2YKxPxeKBXrSj")

MOTS_CLES_RECHERCHE = ["Women Dress", "Lady Dress", "Women clothing"]

# Liste des noms de méthodes alternatifs à tester sur l'API Alibaba ICBU
METHODES_TESTEES = [
    "alibaba.product.search",
    "alibaba.product.list",
    "alibaba.icbu.product.list",
    "alibaba.crossborder.product.search"
]

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

def executer_requete_alibaba(method_name, extra_params=None):
    timestamp = str(int(time.time() * 1000))
    payload = {
        "app_key": APP_KEY,
        "timestamp": timestamp,
        "format": "json",
        "v": "2.0",
        "sign_method": "md5",
        "method": method_name
    }
    
    if extra_params:
        payload.update(extra_params)
        
    payload["sign"] = generer_signature(payload, APP_SECRET)
    
    url = "https://api.alibaba.com/router/rest"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
        "Host": "api.alibaba.com"
    }

    try:
        response = requests.post(url, data=payload, headers=headers, timeout=20)
        if response.status_code == 200:
            data = response.json()
            if "error_response" not in data:
                return data
            else:
                print(f"   ↪️ {method_name} -> Refusé : {data['error_response'].get('sub_msg', data['error_response'].get('msg'))}")
    except Exception as e:
        print(f"⚠️ Erreur réseau pour {method_name} : {e}")
        
    return None

def generate_update_stock_alibaba_json():
    print("🚀 Recherche de la méthode API valide pour le catalogue Alibaba...")

    # Trouver la bonne méthode fonctionnelle
    methode_valide = None
    for methode in METHODES_TESTEES:
        print(f"🧪 Test de la méthode : {methode}")
        res = executer_requete_alibaba(methode, {"keywords": "Women Dress", "page_size": 5, "page_no": 1})
        if res and "error_response" not in res:
            methode_valide = methode
            print(f"✅ Méthode validée avec succès : {methode_valide}")
            break
            
    if not methode_valide:
        print("❌ Aucune des méthodes testées n'a fonctionné directement. Veuillez consulter l'« Explorateur d'API » dans votre console Alibaba pour copier le nom exact de la méthode de recherche.")
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
            print(f"⚠️ Lecture du fichier existant impossible : {e}")

    tous_les_produits = produits_existants.copy()
    produits_trouves = 0

    for keyword in MOTS_CLES_RECHERCHE:
        print(f"🔍 Recherche Alibaba ICBU pour le mot-clé : '{keyword}'")
        search_response = executer_requete_alibaba(methode_valide, {
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
