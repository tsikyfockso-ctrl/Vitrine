import os
import re
import json
import requests
from html.parser import HTMLParser

# ---------------------------------------------------------------------------
# 1. Configuration des variables d'environnement (Secrets)
# ---------------------------------------------------------------------------
CJ_API_KEY = os.getenv("CJ_API_KEY")
GOOGLE_SCRIPT_URL = os.getenv("GOOGLE_SCRIPT_URL")
LOCAL_HTML_FILE = "CJ dropshipping.html"

# ---------------------------------------------------------------------------
# 2. Parser HTML natif (sans dépendance externe bs4)
# ---------------------------------------------------------------------------
class SimpleCJHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.description = ""
        self.og_image = ""
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "title":
            self.in_title = True
        elif tag == "meta":
            if attrs_dict.get("name") == "description":
                self.description = attrs_dict.get("content", "")
            elif attrs_dict.get("property") == "og:image":
                self.og_image = attrs_dict.get("content", "")

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title and not self.title:
            self.title = data.strip()

# ---------------------------------------------------------------------------
# 3. Fonction d'authentification API CJ Dropshipping
# ---------------------------------------------------------------------------
def get_cj_access_token():
    if not CJ_API_KEY:
        print("⚠️ Aucune clé CJ_API_KEY trouvée dans les secrets.")
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
            print(f"⚠️ Erreur token CJ : {res_data.get('message')}")
            return None
    except Exception as e:
        print(f"❌ Erreur connexion API CJ : {e}")
        return None

# ---------------------------------------------------------------------------
# 4. Lecture et extraction du HTML local
# ---------------------------------------------------------------------------
def parse_cj_html_file(file_path):
    if not os.path.exists(file_path):
        print(f"⚠️ Fichier local {file_path} introuvable.")
        return None

    print(f"📄 Analyse du fichier local : {file_path}...")
    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    parser = SimpleCJHTMLParser()
    parser.feed(html_content)

    title = parser.title.split("- CJdropshipping")[0].strip() if parser.title else "Produit Sans Nom"
    desc_text = parser.description
    main_img = parser.og_image

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
        "stock": 100
    }

# ---------------------------------------------------------------------------
# 5. Formattage 22 Colonnes (BDD_Mayah_Store)
# ---------------------------------------------------------------------------
def build_bdd_row(product_data, default_price="15.00"):
    row = [""] * 22
    row[0] = product_data.get("nom", "")

    # Tailles (Cols B-G)
    sizes = product_data.get("sizes", [])
    for i in range(min(len(sizes), 6)):
        row[1 + i] = sizes[i]

    # Prix par taille (Cols H-M)
    for i in range(min(len(sizes), 6)):
        row[7 + i] = default_price

    # Images par couleur (Cols N-T)
    colors = product_data.get("colors", [])
    main_img = product_data.get("main_img", "")
    for i in range(min(max(len(colors), 1), 7)):
        row[13 + i] = main_img

    # Détails (Col U) & Stock (Col V)
    row[20] = product_data.get("details", "")
    row[21] = str(product_data.get("stock", 0))

    return row

# ---------------------------------------------------------------------------
# 6. Envoi vers Google Sheet
# ---------------------------------------------------------------------------
def send_to_google_sheet(row_data):
    if not GOOGLE_SCRIPT_URL:
        print("❌ GOOGLE_SCRIPT_URL non configuré.")
        return False

    print("🚀 Envoi vers Google Sheet...")
    payload = {"row": row_data}
    try:
        response = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=15)
        res_json = response.json()
        if res_json.get("status") == "success":
            print("✨ Données ajoutées avec succès à votre BDD Google Sheet !")
            return True
        else:
            print(f"⚠️ Erreur Google Script : {res_json.get('message')}")
            return False
    except Exception as e:
        print(f"❌ Erreur envoi HTTP : {e}")
        return False

# ---------------------------------------------------------------------------
# Exécution
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("🤖 Démarrage de la synchronisation...")
    token = get_cj_access_token()
    product_info = parse_cj_html_file(LOCAL_HTML_FILE)

    if product_info:
        formatted_row = build_bdd_row(product_info)
        send_to_google_sheet(formatted_row)
    else:
        print("❌ Aucun produit trouvé à synchroniser.")
