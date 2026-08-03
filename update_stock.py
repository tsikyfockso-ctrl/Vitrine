import os
import json
import requests
from deep_translator import GoogleTranslator

CJ_API_KEY = os.environ.get("CJ_API_KEY")

def get_cj_access_token():
    url = "https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken"
    headers = {"Content-Type": "application/json"}
    payload = {"apiKey": CJ_API_KEY}
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("result"):
                return data.get("data", {}).get("accessToken")
    except Exception as e:
        print(f"Erreur d'authentification CJ : {e}")
    return None
    
#recuperation vetement pour femme
def fetch_cj_products_by_sku(token, target_sku):
    url = "https://developers.cjdropshipping.com/api2.0/v1/product/list"
    headers = {
        "CJ-Access-Token": token,
        "Content-Type": "application/json"
    }
    # On récupère une liste générale de la catégorie (ex: women clothing)
    params = {"keyword": "women clothing", "pageSize": 50} 
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            products = data.get("data", {}).get("list", [])
            
            # --- FILTRAGE LOCAL PAR SKU ---
            # On cherche dans la liste celui qui correspond exactement au SKU souhaité
            for product in products:
                sku_produit = product.get("productSku") or product.get("sku") or ""
                if target_sku.lower() in sku_produit.lower():
                    return [product] # Retourne le produit trouvé sous forme de liste
                    
    except Exception as e:
        print(f"Erreur lors de la recherche par SKU : {e}")
        
    return []

def traduire_texte(texte):
    """Traduit automatiquement n'importe quel texte (chinois, etc.) en Français"""
    if not texte or not isinstance(texte, str):
        return "Produit sans nom"
    try:
        traducteur = GoogleTranslator(source='auto', target='fr')
        resultat = traducteur.translate(texte)
        return resultat if resultat else texte
    except Exception as e:
        return texte

def generate_update_stock_json():
    print("🤖 Synchronisation, application des tarifs et traduction automatique en Français...")
    
    token = get_cj_access_token()
    if not token:
        print("❌ Impossible d'obtenir le token d'accès CJ.")
        return

    products_raw = fetch_cj_products_deep(token)
    processed_products = []

    for product in products_raw:
        # --- RÉCUPÉRATION DU SKU ---
        # CJ stocke généralement le SKU principal dans 'productSku' ou 'sku'
        sku_produit = product.get("productSku") or product.get("sku") or "SKU-INCONNU"

        # --- TRADUCTION AUTOMATIQUE DU NOM DU PRODUIT ---
        nom_brut = product.get("productName", "Produit sans nom")
        nom = traduire_texte(nom_brut)
        
        # Gestion des variantes / prix / stock
        variants = product.get("variants", [])
        tailles_values = []
        prix_values = []
        images_values = []
        total_stock = 0
        details_list = []

        if variants:
            for v in variants:
                nom_variante_brut = v.get("variantName", "")
                nom_variante = traduire_texte(nom_variante_brut) if nom_variante_brut else "Standard"
                
                tailles_values.append(nom_variante)
                prix_values.append(str(v.get("variantPrice", "0")))
                images_values.append(v.get("variantImage", ""))
                total_stock += int(v.get("variantStock", 0))
        else:
            tailles_values.append("Standard")
            prix_values.append(str(product.get("sellPrice", "0")))
            images_values.append(product.get("productImage", ""))
            total_stock = product.get("totalStock", 100)

        # Récupération du poids du produit en grammes
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

        # Construction de l'objet produit final avec le SKU inclus
        product_obj = {
            "sku": sku_produit,  # <-- Ajout du SKU ici
            "nom": nom,
            "tailles": tailles_values,
            "prix": prix_values,
            "images": images_values,
            "details": " | ".join(filter(None, details_list)),
            "stock": total_stock,
            "poids": poids_grammes,
            "shippingBase": round(port_final_fr, 2), 
            "shippingUS": round(port_final_us, 2)    
        }
        processed_products.append(product_obj)

    # Écriture dans le fichier JSON local
    with open("update_stock.json", "w", encoding="utf-8") as f:
        json.dump(processed_products, f, ensure_ascii=False, indent=4)

    print(f"✅ Succès : {len(processed_products)} produits traduits, avec SKU, et synchronisés dans update_stock.json")

if __name__ == "__main__":
    generate_update_stock_json()
