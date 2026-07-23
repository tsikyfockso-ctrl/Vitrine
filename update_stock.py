import json
import os
import requests
import iop

# Récupération des secrets configurés dans GitHub
APP_KEY = os.getenv("ALIEXPRESS_APP_KEY")
APP_SECRET = os.getenv("ALIEXPRESS_APP_SECRET")
SESSION_TOKEN = os.getenv("ALIEXPRESS_ACCESS_TOKEN", "50000500a01OR1716b4e49AgApxMpEB4KXeqri0pD9FjygrxweoGMgxftVTZmguw7YY2")

# URL de la passerelle officielle AliExpress (Singapour / Global)
GATEWAY_URL = "https://api-sg.aliexpress.com/sync"
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
  print("Démarrage de la synchronisation avec l'API Dropshipping AliExpress...")

  if not APP_KEY or not APP_SECRET:
    print("Erreur : Les clés APP_KEY ou APP_SECRET sont manquantes.")
    exit(1)

  try:
    # Initialisation du client officiel IOP d'Alibaba/AliExpress
    client = iop.IopClient(GATEWAY_URL, APP_KEY, APP_SECRET)

    # Création de la requête API
    request = iop.IopRequest("aliexpress.ds.product.get")

    # Ajout du jeton de session (access_token)
    request.add_api_param("session", SESSION_TOKEN)

    # Paramètres métier de l'API Dropshipping
    request.add_api_param("product_id", "1005001234567890")
    request.add_api_param("target_currency", "EUR")
    request.add_api_param("target_language", "FR")
    request.add_api_param("ship_to_country", "FR")

    # Exécution de la requête (le SDK gère la signature automatiquement)
    response = client.execute(request)

    # Conversion de la réponse en dictionnaire Python
    response_data = {
        "code": response.code,
        "type": response.type,
        "message": response.message,
        "body": response.body,
    }

    print("Réponse reçue d'AliExpress :")
    print(json.dumps(response_data, indent=4))

    if response_data:
      print("Envoi des données vers le Google Sheet...")
      send_to_google_sheet(response_data)

  except Exception as e:
    print(f"Erreur lors de l'appel au SDK AliExpress : {e}")
