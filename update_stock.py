import os
import json
import requests
from deep_translator import GoogleTranslator

# Configuration avec l'API Key moderne de CJ Dropshipping
CJ_API_KEY = os.environ.get("CJ_API_KEY")

def get_cj_access_token():
    url = "https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken"
    headers = {"Content-Type": "application/json"}
    
    if not CJ_API_KEY:
        print("❌ Erreur : La variable d'environnement CJ_API_KEY n'est pas définie dans les Secrets GitHub.")
        return None

    payload = {"apiKey": CJ_API_KEY}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("result"):
                return data.get("data", {}).get("accessToken")
            else:
                print(f"❌ Erreur API CJ (Token) : {data.get('message', 'Réponse invalide')}")
    except Exception as e:
        print(f"Erreur d'authentification CJ : {e}")
    return None

def fetch_cj_products_stable(token):
    """
    Récupère la liste stable des produits CJ avec recherche ciblée 'women dress'
    """
    url = "https://developers.cjdropshipping.com/api2.0/v1/product/list"
    headers = {
        "CJ-Access-Token": token,
        "Content-Type": "application/json"
    }
    
    params = {
        "keyword": "women dress",
        "pageSize": 20
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get("result"):
                return data.get("data", {}).get("list", [])
    except Exception as e:
        print(f"Erreur lors de la récupération des produits : {e}")
        
    return []

def traduire_texte(texte):
    if not texte:
        return ""
    try:
        return GoogleTranslator(source='auto', target='fr').translate(texte)
    except Exception:
        return texte

def generate_update_stock_json():
    print("🤖 Démarrage du script stable et validé avec extraction des variantes...")
    
    token = get_cj_access_token()
    if not token:
        print("❌ Impossible de continuer sans token CJ.")
        return

    products = fetch_cj_products_stable(token)
    if not products:
        print("⚠️ Aucun produit récupéré.")
        return

    formatted_products = []
    seen_skus = set()

    for product in products:
        sku = product.get("productSku") or product.get("sku")
        if not sku or sku in seen_skus:
            continue
        seen_skus.add(sku)

        # 2. Nom du produit traduit
        nom_original = product.get("productName", "Produit sans titre")
        nom_traduite = traduire_texte(nom_original)

        # 4. Prix de base et prix variants
        sell_price = float(product.get("sellPrice", 0.0))

        # 5. Poids, tailles et longueurs
        poids_grammes = float(product.get("productWeight", 300))
        
        # Extraction des attributs si présents dans le produit
        variants_list = product.get("variants", [])
        tailles = []
        couleurs = []
        prix_variants = [sell_price]

        if isinstance(variants_list, list) and len(variants_list) > 0:
            for v in variants_list:
                s = v.get("variantSize") or v.get("size")
                c = v.get("variantColor") or v.get("color")
                p = v.get("variantPrice")
                if s and s not in tailles:
                    tailles.append(s)
                if c and c not in couleurs:
                    couleurs.append(c)
                if p:
                    try:
                        p_val = float(p)
                        if p_
