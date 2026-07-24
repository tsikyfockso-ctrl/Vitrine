import json
import os
import requests
from aliexpress_api import AliexpressApi, models

# Récupération des secrets configurés dans GitHub
APP_KEY = os.getenv("ALIEXPRESS_APP_KEY")
APP_SECRET = os.getenv("ALIEXPRESS_APP_SECRET")
ACCESS_TOKEN = os.getenv("ALIEXPRESS_ACCESS_TOKEN", "50000500a01OR1716b4e49AgApxMpEB4KXeqri0pD9FjygrxweoGMgxftVTZmguw7YY2")

GOOGLE_SCRIPT_URL = os.getenv("GOOGLE_SCRIPT_URL", "https://script.google.com/macros/s/AKfycbyOxZJjlRvmrw2U-al4CZa8ZsW4FsWwRkH9cMvRig84qqpwr0rp3lsnfpnjGjOAl8Xm/exec")


def send_to_google_sheet(data):
  if not GOOGLE_SCRIPT_URL:
    print("Avertissement : L'URL Google Apps Script n'est pas configurée.")
    return

  try:
    response = requests.post(GOOGLE_SCRIPT_URL, json=data)
    print(f"Réponse de Google Apps Script : {response.text}")
  except Exception as e:
    print(f"Erreur lors de l'envoi vers Google Sheet : {e}")


if __name__ == "__main__":
  print("Démarrage de la synchronisation avec l'API AliExpress...")

  if not APP_KEY or not APP_SECRET:
    print("Erreur : Les clés APP_KEY ou APP_SECRET sont manquantes.")
    exit(1)

  try:
    # Initialisation du client officiel de l'API AliExpress
    # (Utilisation des classes de configuration de langue et devise)
    aliexpress = AliexpressApi(
        APP_KEY,
        APP_SECRET,
        models.Language.FR,
        models.Currency.EUR,
        app_signature=ACCESS_TOKEN,
    )

    # Récupération des détails d'un produit (exemple avec un ID de test ou catalogue)
    product_ids = ["1005001234567890"]
    products = aliexpress.get_products_details(product_ids)

    # Conversion des résultats en format JSON exploitable
    response_data = {
        "status": "success",
        "products": [p.__dict__ for p in products] if products else [],
    }

    print("Réponse reçue d'AliExpress :")
    print(json.dumps(response_data, indent=4, default=str))

    if response_data:
      print("Envoi des données vers le Google Sheet...")
      send_to_google_sheet(response_data)

  except Exception as e:
    print(f"Erreur lors de l'appel à l'API AliExpress : {e}")
