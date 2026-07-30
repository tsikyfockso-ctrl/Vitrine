import os
import re
import json
import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# 1. Configuration des variables d'environnement (Secrets & Variables)
# ---------------------------------------------------------------------------
CJ_API_KEY = os.getenv("CJ_API_KEY")
GOOGLE_SCRIPT_URL = os.getenv("GOOGLE_SCRIPT_URL")

# Mode démo / fallback si la clé API n'est pas encore définie
LOCAL_HTML_FILE = "CJ dropshipping.html"

# ---------------------------------------------------------------------------
# 2. Fonction d'authentification API CJ Dropshipping
# ---------------------------------------------------------------------------
def get_cj_access_token():
    """Génère un jeton d'accès auprès de CJ Dropshipping via la Clé API."""
    if not CJ_API_KEY:
        print("⚠️ Aucune clé CJ_API_KEY trouvée dans les variables d'environnement.")
        return None

    url = "https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken"
    headers = {"Content-Type": "application/json"}
    payload = {"apiKey": CJ_API_KEY}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        res_data = response.json()
        if res_data.get("code") == 200 and res_data.get("result"):
            token = res_data["result"].get("accessToken")
            print("🔑 Jeton d'accès CJ généré avec succès !")
            return token
        else:
            print(f"⚠️ Erreur lors de l'obtention du token CJ : {res_data.get('message')}")
            return None
    except Exception as e:
        print(f"❌ Erreur de connexion API CJ : {e}")
        return None

# ---------------------------------------------------------------------------
# 3. Parsing du fichier HTML local (CJ dropshipping.html)
# ---------------------------------------------------------------------------
def parse_cj_html_file(file_path):
    """Extrait les informations détaillées depuis le fichier HTML local."""
    if not os.path.exists(file_path):
        print(f"⚠️ Fichier local {file_path} introuvable.")
        return None

    print(f"📄 Analyse du fichier local : {file_path}...")
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    # Nom du produit
    title_tag = soup.find("title")
    title = title_tag.text.split("- CJdropshipping")[0].strip() if title_tag else "Produit Sans Nom"

    # Extraction description, couleurs et tailles depuis les balises meta
    desc_tag = soup.find("meta", {"name": "description"})
    desc_text = desc_tag.get("content", "") if desc_tag else ""

    # Image principale
    img_tag = soup.find("meta", {"property": "og:image"})
    main_img = img_tag.get("content", "") if img_tag else ""

    # Extraction des couleurs
    colors = []
    color_match = re.search(r"Color:\s*([^,]+(?:,\s*[^,]+)*)", desc_text, re.IGNORECASE)
    if color_match:
        colors_str = color_match.group(1).split("Size:")[0].strip()
        colors = [c.strip() for c in colors_str.split(",") if c.strip()]

    # Extraction des tailles
    sizes = []
    size_match = re.search(r"Size:\s*([\d\s,XSLM]+)", desc_text, re.IGNORECASE)
    if size_match:
        sizes = [s.strip() for s in size_match.group(1).split(",") if s.strip()]

    return {
        "nom": title,
        "details": desc_text,
        "main_img": main_img,
        "colors": colors,
        "sizes": sizes,
        "stock": 100 # Stock par défaut si non spécifié
    }

# ---------------------------------------------------------------------------
# 4. Construction de la ligne au format exact BDD_Mayah_Store (22 Colonnes)
# ---------------------------------------------------------------------------
def build_bdd_row(product_data, default_price="15.00"):
    """
    Construit un tableau de 22 éléments correspondant exactement aux colonnes A à V :
    [0] Nom
    [1..6] Tailles (Pointures 36, 37, 38, 39, 41, 42 ou XS, S, M, L, XL, XXL)
    [7..12] Prix par tailles
    [13..19] Images par couleur (jusqu'à 7 images)
    [20] Détails
    [21] Nombre de stock disponible
    """
    row = [""] * 22

    # Colonne A : Nom
    row[0] = product_data.get("nom", "")

    # Colonnes B à G : Tailles (max 6)
    sizes = product_data.get("sizes", [])
    for i in range(min(len(sizes), 6)):
        row[1 + i] = sizes[i]

    # Colonnes H à M : Prix par tailles (max 6)
    for i in range(min(len(sizes), 6)):
        row[7 + i] = default_price

    # Colonnes N à T : Images par couleur (max 7)
    colors = product_data.get("colors", [])
    main_img = product_data.get("main_img", "")
    for i in range(min(max(len(colors), 1), 7)):
        row[13 + i] = main_img

    # Colonne U : Détails
    row[20] = product_data.get("details", "")

    # Colonne V : Nombre de stock disponible
    row[21] = str(product_data.get("stock", 0))

    return row

# ---------------------------------------------------------------------------
# 5. Envoi vers Google Sheet (Google Apps Script Web App)
# ---------------------------------------------------------------------------
def send_to_google_sheet(row_data):
    """Envoie la ligne structurée vers Google Apps Script."""
    if not GOOGLE_SCRIPT_URL:
        print("❌ GOOGLE_SCRIPT_URL non configuré dans les secrets.")
        return False

    print("🚀 Envoi des données vers Google Sheet...")
    payload = {"row": row_data}
    
    try:
        response = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=15)
        res_json = response.json()
        if res_json.get("status") == "success":
            print("✨ Données ajoutées avec succès dans votre BDD Google Sheet !")
            return True
        else:
            print(f"⚠️ Erreur Google Script : {res_json.get('message')}")
            return False
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi HTTP : {e}")
        return False

# ---------------------------------------------------------------------------
# Execution Principale
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("🤖 Démarrage du script de synchronisation CJ Dropshipping -> Google Sheet...")

    # 1. Tentative d'authentification à l'API CJ
    token = get_cj_access_token()

    # 2. Récupération des données depuis le fichier HTML local
    product_info = parse_cj_html_file(LOCAL_HTML_FILE)

    if product_info:
        # 3. Formatage selon la structure BDD (22 colonnes)
        formatted_row = build_bdd_row(product_info)

        # 4. Transfert des données dans le Google Sheet
        send_to_google_sheet(formatted_row)
    else:
        print("❌ Impossible d'extraire des produits à synchroniser.")
