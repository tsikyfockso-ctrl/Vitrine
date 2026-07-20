import os
import json
import gspread
from google.oauth2.service_account import Credentials

try:
    # 1. Récupérer le secret JSON depuis GitHub
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    
    if not creds_json:
        raise ValueError("Le secret GOOGLE_CREDENTIALS_JSON est introuvable sur GitHub !")

    # 2. Convertir proprement le texte JSON en dictionnaire Python
    creds_dict = json.loads(creds_json)

    # 3. Définir les permissions nécessaires (Sheets + Drive)
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    # 4. Authentification directe via les credentials du compte de service
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)

    # 5. Ouvrir votre Google Sheet "BDD_Mayah_Store"
    sheet = client.open("BDD_Mayah_Store").sheet1

    # 6. Ajouter une ligne de test automatique
    nouveau_produit = ["Produit Test AliExpress", "19.99", "https://url-image.jpg"]
    sheet.append_row(nouveau_produit)

    print("Succès : Le stock a été mis à jour dans BDD_Mayah_Store !")

except Exception as e:
    print(f"Erreur critique : {e}")
    exit(1)
