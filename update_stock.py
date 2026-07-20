import os
import json
import gspread
from google.oauth2.service_account import Credentials

try:
    scope = ["https://docs.google.com/spreadsheets/d/1jtPRVyTlctnwKIWphULrT2SjcZtsm-BYEILlYOGeai0/edit?usp=sharing"]
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    
    if not creds_json:
        raise ValueError("Le secret GOOGLE_CREDENTIALS_JSON est introuvable !")

    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)

    # Remplacez par le nom exact de votre Google Sheet
    sheet = client.open("BDD_Mayah_Store").sheet1

    # Exemple d'ajout de produit automatisé
    nouveau_produit = ["Nom du produit", "29.99", "https://url-image.jpg"]
    sheet.append_row(nouveau_produit)

    print("Stock mis à jour avec succès !")

except Exception as e:
    print(f"Erreur : {e}")
    exit(1)
