import os
import json
import requests

# ---------------------------------------------------------------------------
# 1. Variables d'environnement (GitHub Secrets)
# ---------------------------------------------------------------------------
CJ_API_KEY = os.getenv("CJ_API_KEY")
GOOGLE_SCRIPT_URL = os.getenv("GOOGLE_SCRIPT_URL")

# ---------------------------------------------------------------------------
# 2. Authentification API CJ Dropshipping
# ---------------------------------------------------------------------------
def get_cj_access_token():
    """Obtient le jeton d'accès via la Clé API CJ Dropshipping."""
    if not CJ_API_KEY:
        print("❌ Clé CJ_API_KEY manquante dans les Secrets.")
        return None

    url = "https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken"
    headers = {"Content-Type": "application/json"}
    payload = {"apiKey": CJ_API_KEY}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        res_data = response.json()
        if res_data.get("code") == 200 and res_data.get("result"):
            token = res_data["result"].get("accessToken")
            print("🔑 Jeton d'accès CJ généré avec succès !")
            return token
        else:
            print(f"⚠️ Erreur Authentification CJ : {res_data.get('message')}")
            return None
    except Exception as e:
        print(f"❌ Erreur connexion API CJ : {e}")
        return None

# ---------------------------------------------------------------------------
# 3. Récupération des produits via l'API CJ Dropshipping
# ---------------------------------------------------------------------------
def get_cj_products(access_token, page_num=1, page_size=10):
    """Récupère la liste des produits depuis l'API CJ."""
    url = f"https://developers.cjdropshipping.com/api2.0/v1/product/list?pageNum={page_num}&pageSize={page_size}"
    headers = {
        "CJ-Access-Token": access_token,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        res_data = response.json()
        if res_data.get("code") == 200 and res_data.get("result"):
            return res_data["result"].get("list", [])
        else:
            print(f"⚠️ Erreur récupération produits CJ : {res_data.get('message')}")
            return []
    except Exception as e:
        print(f"❌ Erreur lors de la requête produits : {e}")
        return []

# ---------------------------------------------------------------------------
# 4. Formatage de la ligne selon la BDD Mayah Store (22 colonnes A à V)
# ---------------------------------------------------------------------------
def build_bdd_row(product):
    """
    Structure les données sur 22 colonnes :
    - Col A (0) : nom
    - Col B..G (1..6) : tailles (ex: 36, 37, 38...)
    - Col H..M (7..12) : prix par tailles
    - Col N..T (13..19) : img par couleur
    - Col U (20) : details
    - Col V (21) : nombre de stock disponible
    """
    row = [""] * 22

    # Nom du produit (Colonne A)
    row[0] = product.get("productNameEn", product.get("productName", ""))

    # Extraction des variantes (Tailles, Prix, Stock)
    variants = product.get("variants", [])
    sizes = []
    prices = []
    images = []
    total_stock = []

    # Image principale
    main_img = product.get("productImage", "")
    if main_img:
        images.append(main_img)

    if variants:
        for v in variants:
            size_val = v.get("variantKey", "") or v.get("variantNameEn", "")
            price_val = str(v.get("variantSellPrice", "0.00"))
            stock_val = v.get("variantStandardQuantity", 0)

            if size_val and size_val not in sizes:
                sizes.append(size_val)
                prices.append(price_val)

            variant_img = v.get("variantImage", "")
            if variant_img and variant_img not in images:
                images.append(variant_img)

            total_stock += int(stock_val) if isinstance(stock_val, (int, str)) and str(stock_val).isdigit() else 0
    else:
        # Si pas de variantes explicites dans la liste
        default_price = str(product.get("sellPrice", "0.00"))
        prices.append(default_price)

    # Colonnes B à G : Tailles (Max 6)
    for i in range(min(len(sizes), 6)):
        row[1 + i] = sizes[i]

    # Colonnes H à M : Prix par tailles (Max 6)
    for i in range(min(len(prices), 6)):
        row[7 + i] = prices[i]

    # Colonnes N à T : Images par couleur (Max 7)
    for i in range(min(len(images), 7)):
        row[13 + i] = images[i]

    # Colonne U : Details
    row[20] = f"SKU: {product.get('productSku', '')} | Catégorie: {product.get('categoryName', '')}"

    # Colonne V : Stock disponible
    row[21] = str(total_stock if total_stock > 0 else 100)

    return row

# ---------------------------------------------------------------------------
# 5. Envoi vers Google Sheet via Google Apps Script
# ---------------------------------------------------------------------------
def send_to_google_sheet(row_data):
    """Envoie une ligne de 22 colonnes vers le WebApp Google Sheet."""
    if not GOOGLE_SCRIPT_URL:
        print("❌ GOOGLE_SCRIPT_URL non configuré.")
        return False

    try:
        response = requests.post(GOOGLE_SCRIPT_URL, json={"row": row_data}, timeout=15)
        res_json = response.json()
        if res_json.get("status") == "success":
            print(f"✅ Enregistré : {row_data[0][:30]}...")
            return True
        else:
            print(f"⚠️ Erreur Apps Script : {res_json.get('message')}")
            return False
    except Exception as e:
        print(f"❌ Erreur envoi HTTP : {e}")
        return False

# ---------------------------------------------------------------------------
# Exécution Principale
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("🤖 Démarrage de la synchronisation CJ Dropshipping -> Google Sheet...")

    token = get_cj_access_token()
    if token:
        products = get_cj_products(token, page_num=1, page_size=10)
        print(f"📦 {len(products)} produits récupérés depuis l'API CJ.")

        for prod in products:
            formatted_row = build_bdd_row(prod)
            send_to_google_sheet(formatted_row)

        print("✨ Synchronisation terminée avec succès !")
    else:
        print("❌ Impossible de démarrer la synchronisation sans jeton valide.")
