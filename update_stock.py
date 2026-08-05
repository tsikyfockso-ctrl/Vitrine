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

def verify_sku_on_cj(token, sku):
    """
    Simule une recherche humaine : teste si le SKU existe et est trouvé sur CJ.
    Retourne True si le produit est valide et trouvé, False sinon.
    """
    if not sku or sku == "N/A":
        return False
        
    url = "https://developers.cjdropshipping.com/api2.0/v1/product/query" # Endpoint de recherche par SKU/détail
    headers = {
        "CJ-Access-Token": token,
        "Content-Type": "application/json"
    }
    # Paramètre pour tester le SKU exact
    params = {"productSku": sku}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            # Si l'API renvoie des données valides pour ce SKU, il existe
            if data.get("result") and data.get("data"):
                return True
    except Exception:
        pass
        
    return False

def fetch_cj_products_deep(token):
    url = "https://developers.cjdropshipping.com/api2.0/v1/product/list"
    headers = {
        "CJ-Access-Token": token,
        "Content-Type": "application/json"
    }
    
    # Recherche stricte et ciblée uniquement sur les robes pour femmes
    params = {
        "keyword": "women dress",
        "pageSize": 40  # On en demande un peu plus pour filtrer ceux qui n'ont pas de SKU valide
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get("data", {}).get("list", [])
    except Exception as e:
        print(f"Erreur de connexion CJ : {e}")
    return []

def traduire_texte(texte):
    """Traduit automatiquement n'importe quel texte en Français"""
    if not texte:
        return ""
    try:
        return GoogleTranslator(source='auto', target='fr').translate(texte)
    except Exception:
        return texte

def generate_update_stock_json():
    print("🤖 Synchronisation, vérification des SKU et traduction (Robes Femmes)...")
    
    token = get_cj_access_token()
    if not token:
        print("❌ Erreur : Impossible d'obtenir le token d'accès CJ.")
        return

    products_raw = fetch_cj_products_deep(token)
    
    formatted_products = []
    for product in products_raw:
        sku = product.get("productSku") or product.get("sku") or "N/A"
        
        # ÉTAPE CLÉ : Le script teste le SKU un par un avant de valider le produit
        print(f"🔍 Test du SKU : {sku}...")
        if not verify_sku_on_cj(token, sku):
            print(f"⚠️ SKU {sku} introuvable ou invalide sur CJ. Produit ignoré.")
            continue  # Ignore ce produit et passe au suivant
            
        print(f"✅ SKU {sku} validé avec succès !")
        
        nom_original = product.get("productName", "Produit sans titre")
        nom_traduite = traduire_texte(nom_original)
        
        # Récupération sécurisée du poids
        try:
            poids_grammes = float(product.get("productWeight", 200))
        except ValueError:
            poids_grammes = 200.0

        # --- TARIF DE LIVRAISON : FRANCE (FR) ---
        if poids_grammes <= 1:
            port_base_fr = 3.54
        elif poids_grammes < 100:
            port_base_fr = 3.54 + (poids_grammes * 0.015)
        elif poids_grammes == 100:
            port_base_fr = 4.05
        elif poids_grammes <= 300:
            port_base_fr = 4.05 + ((poids_grammes - 100) * 0.02525)
        else:
            port_base_fr = 8.10 + ((poids_grammes - 300) * 0.0205)

        port_final_fr = port_base_fr + 0.99

        # --- TARIF DE LIVRAISON : ÉTATS-UNIS (US) ---
        if poids_grammes <= 0.01:
            port_final_us = 6.67
        elif 1 <= poids_grammes <= 50:
            port_final_us = 7.73
        elif poids_grammes == 51:
            port_final_us = 7.76
        elif poids_grammes == 52:
            port_final_us = 7.78
        elif poids_grammes == 53:
            port_final_us = 7.80
        else:
            port_final_us = 7.80 + ((poids_grammes - 53) * 0.02)

        product_obj = {
            "sku": sku,
            "nom": nom_traduite,
            "prix": product.get("sellPrice", 0.0),
            "images": [product.get("productImage", "")],
            "poids": poids_grammes,
            "shippingBase": round(port_final_fr, 2),
            "shippingUS": round(port_final_us, 2)
        }
        formatted_products.append(product_obj)

    if formatted_products:
        with open("update_stock.json", "w", encoding="utf-8") as f:
            json.dump(formatted_products, f, ensure_ascii=False, indent=4)
        print(f"✅ Succès : {len(formatted_products)} robes valides synchronisées dans update_stock.json")
    else:
        print("⚠️ Aucun produit valide avec un SKU vérifié n'a été trouvé.")

if __name__ == "__main__":
    generate_update_stock_json()
