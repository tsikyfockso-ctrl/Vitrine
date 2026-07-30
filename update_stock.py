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
    """Envoie les données structurées vers Google Apps Script en respectant la BDD."""
    try:
        response = requests.post(GOOGLE_SCRIPT_URL, json=payload)
        if response.status_code == 200:
            print(f"   🚀 Ligne insérée avec succès pour : {payload['nom']}")
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
    
    # Référentiel des tailles standard présentes dans votre BDD (Colonnes B à G)
    standard_tailles = ["36", "37", "38", "39", "41", "42"]
    
    for product in products:
        nom = product.get("productNameEn") or product.get("productName", "")
        variants = product.get("variants", [])
        
        # Initialisation des listes pour correspondre aux plages de colonnes exactes
        # Col B à G (Tailles / Stock par taille) -> 6 emplacements
        tailles_values = [""] * 6
        # Col H à M (Prix par taille) -> 6 emplacements
        prix_values = [""] * 6
        # Col N à T (Images par couleur) -> 7 emplacements
        images_values = [""] * 7
        
        details_list = []
        total_stock = 0

        if variants:
            for idx, variant in enumerate(variants):
                v_size = str(variant.get("variantSize", "")).strip()
                v_price = str(variant.get("variantPrice", ""))
                v_image = variant.get("variantImage", "")
                v_stock = variant.get("variantStock", 0)
                v_key = variant.get("variantKey", "")
                
                try:
                    total_stock += int(v_stock)
                except ValueError:
                    pass

                # Placer intelligemment selon la position ou la correspondance de taille
                pos = idx if idx < 6 else 5  # Limité aux 6 colonnes disponibles (B-G)
                
                # Si la taille correspond à un standard de la BDD, on l'aligne
                if v_size in standard_tailles:
                    pos = standard_tailles.index(v_size)

                tailles_values[pos] = v_size
                prix_values[pos] = v_price
                
                if idx < 7:
                    images_values[idx] = v_image
                
                if v_key:
                    details_list.append(v_key)
        else:
            # Produit simple sans variantes multiples
            tailles_values[0] = str(product.get("productSize", ""))
            prix_values[0] = str(product.get("sellPrice", ""))
            images_values[0] = product.get("productImage", "")
            try:
                total_stock = int(product.get("sellStock", 0))
            except ValueError:
                total_stock = 0
            details_list.append(product.get("productSku", ""))

        # Construction du payload final mappé exactement sur votre structure de colonnes (A à V)
        payload = {
            "nom": nom,                          # Colonne A
            "col_B": tailles_values[0],          # Colonne B
            "col_C": tailles_values[1],          # Colonne C
            "col_D": tailles_values[2],          # Colonne D
            "col_E": tailles_values[3],          # Colonne E
            "col_F": tailles_values[4],          # Colonne F
            "col_G": tailles_values[5],          # Colonne G
            "col_H": prix_values[0],             # Colonne H
            "col_I": prix_values[1],             # Colonne I
            "col_J": prix_values[2],             # Colonne J
            "col_K": prix_values[3],             # Colonne K
            "col_L": prix_values[4],             # Colonne L
            "col_M": prix_values[5],             # Colonne M
            "col_N": images_values[0],           # Colonne N
            "col_O": images_values[1],           # Colonne O
            "col_P": images_values[2],           # Colonne P
            "col_Q": images_values[3],           # Colonne Q
            "col_R": images_values[4],           # Colonne R
            "col_S": images_values[5],           # Colonne S
            "col_T": images_values[6],           # Colonne T
            "details": " | ".join(filter(None, details_list)), # Colonne U
            "nombre_de_stock_disponible": str(total_stock)     # Colonne V
        }
        
        send_to_google_sheet(payload)

    print("✨ Synchronisation terminée avec succès !")

if __name__ == "__main__":
    update_stock()
