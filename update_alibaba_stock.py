import os
import json
import requests
import time
import hmac
import hashlib
from deep_translator import GoogleTranslator

APP_KEY = os.environ.get("ALIBABA_APP_KEY", "505290")
APP_SECRET = os.environ.get("ALIBABA_APP_SECRET", "cPs3QbmUQ2MNPAqPIek1hRMENUtyM4pm")
ACCESS_TOKEN = os.environ.get(
    "ALIBABA_ACCESS_TOKEN",
    "50000901138xfbaaykUFnQBSQGfkEvBNxxjfgxmxdUxHjZAvp51cea4168SVn6",
)

# Renseignez ici vos propres model_number ou sku_code enregistrés sur votre compte ICBU
RECHERCHES_PRODUITS = [
    {"model_number": "model", "sku_code": "3523LDS"},
]


def generer_signature_hmac_officielle(api_path, params, secret):
    cleaned_params = {str(k): str(v) for k, v in params.items() if k != "sign"}
    sorted_keys = sorted(cleaned_params.keys())
    query_string = api_path + "".join([f"{k}{cleaned_params[k]}" for k in sorted_keys])
    hmac_obj = hmac.new(secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256)
    return hmac_obj.hexdigest().upper()


def traduire_texte(texte):
    if not texte:
        return "Nom indisponible"
    try:
        trads = GoogleTranslator(source="auto", target="fr").translate(str(texte).strip())
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
        "access_token": ACCESS_TOKEN,
    }

    if extra_params:
        payload.update({k: v for k, v in extra_params.items() if v is not None and v != ""})

    payload["sign"] = generer_signature_hmac_officielle(api_path, payload, APP_SECRET)

    url = f"https://openapi-api.alibaba.com/rest{api_path}"
    try:
        response = requests.get(url, params=payload, timeout=20)
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

    for critere in RECHERCHES_PRODUITS:
        print(f"🔍 Recherche Alibaba avec critères : {critere}")
        params_requete = {
            "page_index": "1",
            "page_size": "20",
        }
        params_requete.update(critere)

        search_response = executer_requete_alibaba(api_path, params_requete)
        if not search_response:
            continue

        result_data = search_response.get("result", search_response)
        items = result_data.get("products", result_data.get("resultList", result_data.get("data", [])))

        for item in items:
            basic_info = item.get("basic_info", item)
            pid = str(basic_info.get("product_id") or item.get("productId") or item.get("id") or "")
            if not pid:
                continue

            produits_trouves += 1
            nom_original = basic_info.get("subject") or item.get("subject") or item.get("title") or "Produit Alibaba"
            nom_fr = traduire_texte(nom_original)

            images = []
            for img in item.get("product_images", []) or []:
                if isinstance(img, dict) and img.get("image_url"):
                    images.append(img["image_url"])
            if not images:
                raw_imgs = item.get("images") or item.get("imageUrlList") or [item.get("imageUrl", "")]
                images = [img for img in raw_imgs if img]

            prix_base = float(item.get("price") or item.get("salePrice") or 0.0)

            tous_les_produits[pid] = {
                "dropshipping": "Alibaba",
                "pid": pid,
                "nom": nom_fr,
                "prixBase": round(prix_base, 2),
                "images": images,
                "variantes": [
                    {
                        "sku": critere.get("sku_code", pid),
                        "vid": pid,
                        "taille": "Standard",
                        "couleur": "Unique",
                        "prix": prix_base,
                        "poids": 0.5,
                        "stock": int(item.get("stock", 100)),
                        "shippingMethodFR": "Alibaba Standard Shipping",
                        "shippingCostFR": 0.0,
                        "shippingMethodUS": "Alibaba Standard Shipping",
                        "shippingCostUS": 0.0,
                    }
                ],
            }

    resultat_final = list(tous_les_produits.values())
    with open("update_alibaba_stock.json", "w", encoding="utf-8") as f:
        json.dump(resultat_final, f, ensure_ascii=False, indent=4)

    print(
        f"🎉 Synchronisation terminée : {len(resultat_final)} produits enregistrés dans "
        f"update_alibaba_stock.json (Nouveaux: {produits_trouves})"
    )


if __name__ == "__main__":
    generate_update_stock_alibaba_json()
