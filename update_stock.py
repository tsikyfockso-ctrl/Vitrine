import hashlib
import hmac
import json
import os
import time
import requests

# Récupération des secrets configurés dans GitHub
APP_KEY = os.getenv("ALIEXPRESS_APP_KEY")
APP_SECRET = os.getenv("ALIEXPRESS_APP_SECRET")
ACCESS_TOKEN = os.getenv("ALIEXPRESS_ACCESS_TOKEN", "50000500a01OR1716b4e49AgApxMpEB4KXeqri0pD9FjygrxweoGMgxftVTZmguw7YY2")

GATEWAY_URL = "https://api-sg.aliexpress.com/sync"
GOOGLE_SCRIPT_URL = os.getenv("GOOGLE_SCRIPT_URL", "https://script.google.com/macros/s/AKfycbyOxZJjlRvmrw2U-al4CZa8ZsW4FsWwRkH9cMvRig84qqpwr0rp3lsnfpnjGjOAl8Xm/exec")


def generate_sign(params, secret):
  """Génère la signature HMAC-SHA256 officielle d'AliExpress en triant

  strictement tous les paramètres par ordre alphabétique de leurs clés.
  """
  filtered_params = {
      k: str(v) for k, v in params.items() if k != "sign" and v is not None
  }
  sorted_params = sorted(filtered_params.items())

  query_string = "".join(f"{k}{v}" for k, v in sorted_params)
  base_string = secret + query_string + secret

  return (
      hmac.new(
          secret.encode("utf-8"),
          base_string.encode("utf-8"),
          hashlib.sha256,
      )
      .hexdigest()
      .upper()
  )


def call_aliexpress_api(api_method, business_params):
  """Exécute une requête sécurisée vers l'API AliExpress Dropshipping."""
  timestamp = str(int(time.time() * 1000))

  # Paramètres communs obligatoires
  common_params = {
      "app_key": APP_KEY,
      "timestamp": timestamp,
      "sign_method": "sha256",
      "method": api_method,
      "partner_id": "sdk-python-2.0",
      "format": "json",
      "access_token": ACCESS_TOKEN,
  }

  # Fusion des paramètres communs et professionnels
  all_params = {**common_params, **business_params}

  # Génération de la signature sur l'ensemble global
  all_params["sign"] = generate_sign(all_params, APP_SECRET)

  try:
    response = requests.post(GATEWAY_URL, data=all_params)
    result = response.json()
    return result
  except Exception as e:
    print(f"Erreur de connexion à l'API AliExpress : {e}")
    return None


def send_to_google_sheet(data):
  """Envoie les données récupérées vers votre Google Sheet via Apps Script."""
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
    print(
        "Erreur : Les clés APP_KEY ou APP_SECRET ne sont pas définies dans les"
        " secrets."
    )
    exit(1)

  # Paramètres exacts pour l'API Dropshipping d'AliExpress
  # (Vous pouvez remplacer 'product_id' par l'identifiant d'un produit que vous souhaitez suivre)
  payload = {
      "product_id": "1005001234567890",
      "target_currency": "EUR",
      "target_language": "FR",
      "ship_to_country": "FR",
  }

  # Appel de l'API de dropshipping officielle
  response_data = call_aliexpress_api("aliexpress.ds.product.get", payload)

  print("Réponse reçue d'AliExpress :")
  print(json.dumps(response_data, indent=4))

  # Transmission des données vers Google Sheets si la réponse est valide
  if response_data:
    print("Envoi des données vers le Google Sheet...")
    send_to_google_sheet(response_data)
