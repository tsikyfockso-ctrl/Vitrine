import os
import requests

# Récupération des secrets configurés dans GitHub Actions
CJ_API_KEY = os.environ.get("CJ_API_KEY")
GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SHEET_URL") # Mettez ici l'URL de votre application web Apps Script

def fetch_cj_products():
    """Récupère les produits depuis l'API CJ Dropshipping."""
    url = "https://developers.cjdropshipping.com/api2.0/v1/product/list"
    headers = {
        "CJ-Access-Token": CJ_API_KEY,
        "Content-Type": "application/json"
    }
    params = {
        "keyword": "fashion accessories" # Vous pouvez changer ou boucler sur vos mots-clés
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get("data", {}).get("list", [])
        else:
            print(f"Erreur API CJ : {response.status_code}")
            return []
    except Exception as e:
        print(f"Erreur de connexion à l'API CJ : {e}")
        return []

def send_to_google_sheet(product_data):
    """Envoie les données formatées vers votre Google Sheet via Apps Script."""
    try:
        response = requests.post(GOOGLE_SCRIPT_URL, json=product_data)
        if response.status_code == 200:
            print(f"✔️ Envoyé avec succès au Google Sheet : {product_data.get('nom')}")
        else:
            print(f"⚠️ Erreur d'envoi Google Sheet : {response.status_code}")
    except Exception as e:
        print(f"Erreur réseau Google Sheet : {e}")

def update_stock():
    print("🤖 Démarrage de la synchronisation CJ Dropshipping -> Google Sheet (Mayah Store)...")
    
    products = fetch_cj_products()
    print(f"📦 {len(products)} produits trouvés sur CJ.")
    
    for product in products:
        # Correspondance exacte avec les colonnes de votre BDD_Mayah_Store
        nom = product.get("productName", "Nom indisponible")
        img_url = product.get("productImage", "")
        stock = product.get("sellStock", 0)
        
        # Structure envoyée pour correspondre à votre Google Sheet
        payload = {
            "nom": nom,
            "taille": "Standard", # Ajustez selon les variantes si disponibles
            "prix": product.get("sellPrice", "0"),
            "img": img_url,
            "details": product.get("productSku", ""),
            "stock": str(stock)
        }
        
        send_to_google_sheet(payload)

    print("✨ Synchronisation terminée avec succès !")

if __name__ == "__main__":
    update_stock()
