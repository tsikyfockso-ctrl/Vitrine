import os
import requests

# Récupération des secrets configurés dans GitHub Actions ou votre environnement
CJ_API_KEY = os.environ.get("CJ_API_KEY")
GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SCRIPT_URL")

def get_cj_access_token():
    """Génère le jeton d'accès valide pour l'API CJ via l'API Key."""
    url = "https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken"
    headers = {"Content-Type": "application/json"}
    payload = {"apiKey": CJ_API_KEY}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("result"):
                return data.get("data", {}).get("accessToken")
        print(f"⚠️ Erreur d'authentification CJ : {response.text}")
    except Exception as e:
        print(f"Erreur réseau lors de l'authentification : {e}")
    return None

def fetch_cj_products_deep(token):
    """Recherche des produits et de leurs variantes réelles sur CJ Dropshipping."""
    url = "https://developers.cjdropshipping.com/api2.0/v1/product/list"
    headers = {
        "CJ-Access-Token": token,
        "Content-Type": "application/json"
    }
    params = {"keyword": "fashion accessories"}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        print(f"📊 Code HTTP reçu de CJ : {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            return data.get("data", {}).get("list", [])
        else:
            print(f"Erreur API CJ : {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Erreur de connexion à l'API CJ : {e}")
        return []

def send_to_google_sheet(payload):
    """Envoie les données structurées vers Google Apps Script en respectant la matrice de la BDD."""
    try:
        response = requests.post(GOOGLE_SCRIPT_URL, json=payload)
        if response.status_code == 200:
            print(f"   🚀 Envoyé : {payload['nom']} | Tailles/Matrice remplie | Stock: {payload['nombre_de_stock_disponible']}")
        else:
            print(f"   ⚠️ Erreur Google Sheet ({response.status_code}) - {response.text}")
    except Exception as e:
        print(f"   Erreur réseau Google Sheet : {e}")

def update_stock():
    print("🤖 Démarrage de la synchronisation CJ Dropshipping -> BDD_Mayah_Store...")
    
    token = get_cj_access_token()
    if not token:
        print("❌ Arrêt du script : Impossible d'obtenir le jeton d'accès CJ.")
        return
    
    products = fetch_cj_products_deep(token)
    print(f"📦 {len(products)} produits principaux trouvés sur CJ.")
    
    for product in products:
        nom = product.get("productNameEn") or product.get("productName", "")
        variants = product.get("variants", [])
        
        # Mapping pour faire correspondre les tailles aux colonnes horizontales de votre BDD
        # Colonnes de base de votre fichier : 'taille', 'Unnamed: 2', 'Unnamed: 3', 'Unnamed: 4', 'Unnamed: 5', 'Unnamed: 6'
        tailles_list = ["36", "37", "38", "39", "41", "42"] # ou ["XS", "S", "M", "L", "XL", "XXL"]
        
        stock_par_taille = {}
        prix_par_taille = {}
        img_par_couleur = ""
        details_sku = ""

        if variants:
            for variant in variants:
                v_size = str(variant.get("variantSize", "")).strip()
                stock_par_taille[v_size] = str(variant.get("variantStock", ""))
                prix_par_taille[v_size] = str(variant.get("variantPrice", ""))
                if not img_par_couleur:
                    img_par_couleur = variant.get("variantImage", "")
                details_sku = variant.get("variantKey", "")
        else:
            v_size = str(product.get("productSize", "")).strip()
            stock_par_taille[v_size] = str(product.get("sellStock", ""))
            prix_par_taille[v_size] = str(product.get("sellPrice", ""))
            img_par_couleur = product.get("productImage", "")
            details_sku = product.get("productSku", "")

        # Construction du payload adapté à votre structure horizontale
        payload = {
            "nom": nom,
            # Distribution des tailles sur les colonnes correspondantes de votre BDD
            "taille": stock_par_taille.get(tailles_list[0], ""),
            "col_taille_2": stock_par_taille.get(tailles_list[1], ""),
            "col_taille_3": stock_par_taille.get(tailles_list[2], ""),
            "col_taille_4": stock_par_taille.get(tailles_list[3], ""),
            "col_taille_5": stock_par_taille.get(tailles_list[4], ""),
            "col_taille_6": stock_par_taille.get(tailles_list[5], ""),
            
            "prix_par_tailles": str(list(prix_par_taille.values())[0]) if prix_par_taille else "",
            "img_par_couleur": img_par_couleur,
            "details": details_sku,
            "nombre_de_stock_disponible": sum(int(s) for s in stock_par_taille.values() if s.isdigit())
        }
        
        send_to_google_sheet(payload)

    print("✨ Synchronisation terminée avec succès !")

if __name__ == "__main__":
    update_stock()
