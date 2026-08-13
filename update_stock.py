import os
import json
import requests
from deep_translator import GoogleTranslator

# Clé API CJ (récupérée depuis les secrets GitHub)
CJ_API_KEY = os.environ.get("CJ_API_KEY")
MOTS_CLES_RECHERCHE = ["Lady Dress", "Women Dress", "Dress"]

CJ_AUTH_URL = "https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken"
CJ_PRODUCT_LIST_V2_URL = "https://developers.cjdropshipping.com/api2.0/v1/product/listV2"

def get_cj_access_token():
    headers = {"Content-Type": "application/json"}
    if not CJ_API_KEY:
        print("❌ Erreur : La variable CJ_API_KEY n'est pas définie.")
        return None

    payload = {"apiKey": CJ_API_KEY}
    try:
        response = requests.post(CJ_AUTH_URL, json=payload, headers=headers, timeout=60)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and data.get("result"):
                token_data = data.get("data")
                if isinstance(token_data, dict):
                    return token_data.get("accessToken")
    except Exception as e:
        print(f"Erreur d'authentification CJ : {e}")
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
    except Exception as e:
        print(f"Erreur réseau API GET : {e}")
    return None

def generate_update_stock_json():
    token = get_cj_access_token()
    if not token:
        print("❌ Impossible d'obtenir le token d'accès.")
        return

    items = []
    for keyword in MOTS_CLES_RECHERCHE:
        print(f"🔍 Test de recherche avec le mot-clé : '{keyword}'")
        params = {
            "page": 1,
            "size": 5,
            "keyWord": keyword,
            "features": "enable_description"
        }
        
        raw_response = api_get(CJ_PRODUCT_LIST_V2_URL, token, params=params)
        print(f"📦 Type de réponse brute reçue : {type(raw_response)}")
        
        if raw_response:
            if isinstance(raw_response, dict):
                print(f"🔑 Clés disponibles dans l'objet réponse : {list(raw_response.keys())}")
                items = (
                    raw_response.get("list") or 
                    raw_response.get("productList") or 
                    raw_response.get("content") or 
                    raw_response.get("records") or []
                )
            elif isinstance(raw_response, list):
                items = raw_response

        if items:
            print(f"✅ Trouvé ! {len(items)} éléments dans la liste.")
            # Afficher la structure du premier élément pour comprendre comment l'analyser
            print(f"📄 Aperçu des clés du 1er produit : {list(items[0].keys()) if isinstance(items[0], dict) else 'Format non dict'}")
            break
        else:
            print(f"⚠️ Aucun élément trouvé pour '{keyword}'.")

    formatted_products = []
    for index, item in enumerate(items, start=1):
        try:
            if not isinstance(item, dict):
                print(f"⚠️ L'élément {index} n'est pas un dictionnaire : {type(item)}")
                continue
            
            # Affichage de débogage pour chaque champ testé
            pid = item.get("pid") or item.get("id") or item.get("productId") or item.get("goodsId")
            nom = item.get("productName") or item.get("nameEn") or item.get("name")
            print(f"   -> Produit {index} | PID détecté : {pid} | Nom détecté : {nom}")

            if not pid:
                print(f"   ❌ Ignoré : Aucun PID valide trouvé.")
                continue

            product_obj = {
                "dropshipping": "CJ Dropshipping",
                "sku": str(item.get("sku") or pid).upper(),
                "nom": str(nom or "Produit"),
                "stock": int(item.get("stock") or item.get("inventory") or 0)
            }
            formatted_products.append(product_obj)
            print(f"   ✅ Ajouté avec succès à la liste !")

        except Exception as err:
            print(f"   ❌ Erreur interceptée sur le produit {index}: {err}")
            continue

    with open("update_stock.json", "w", encoding="utf-8") as f:
        json.dump(formatted_products, f, ensure_ascii=False, indent=4)
    print(f"🎉 Terminé : {len(formatted_products)} produits enregistrés dans update_stock.json")

if __name__ == "__main__":
    generate_update_stock_json()
