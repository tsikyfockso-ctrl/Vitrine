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
    
    url = "https://api.taobao.com/router/rest"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
    }

    try:
        response = requests.post(url, data=payload, headers=headers, timeout=20)
        print(f"🔍 Requête {method_name} [Statut {response.status_code}] : {response.text}")
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"⚠️ Erreur réseau pour {method_name} : {e}")
        
    return None

def generate_update_stock_alibaba_json():
    print("🚀 Interrogation du catalogue Alibaba avec diagnostic des méthodes...")

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

    # Testons d'abord avec l'API de recherche standard Alibaba Wholesale / ICBU alternative
    methodes_a_tester = [
        "alibaba.icbu.product.list",
        "alibaba.product.search",
        "com.alibaba.product.search"
    ]

    for method_name in methodes_a_tester:
        print(f"\n🧪 Test de la méthode API : {method_name}")
        search_response = executer_requete_alibaba(method_name, {
            "page_size": 5,
            "page_no": 1
        })
        
        if search_response and "error_response" not in search_response:
            print(✅ Succès avec la méthode : {method_name})
            break
        else:
            print(f"❌ Échec pour {method_name}, passage à la suivante...")

if __name__ == "__main__":
    generate_update_stock_alibaba_json()
