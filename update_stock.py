import hashlib
import hmac
import json
import os
import time
import requests

# Récupération des secrets configurés dans GitHub
APP_KEY = os.getenv("ALIEXPRESS_APP_KEY")
APP_SECRET = os.getenv("ALIEXPRESS_APP_SECRET")
ACCESS_TOKEN = os.getenv("ALIEXPRESS_ACCESS_TOKEN", "https://script.google.com/macros/s/AKfycbyOxZJjlRvmrw2U-al4CZa8ZsW4FsWwRkH9cMvRig84qqpwr0rp3lsnfpnjGjOAl8Xm/exec")

GATEWAY_URL = "https://api-sg.aliexpress.com/sync"
GOOGLE_SCRIPT_URL = os.getenv("GOOGLE_SCRIPT_URL", "50000500a01OR1716b4e49AgApxMpEB4KXeqri0pD9FjygrxweoGMgxftVTZmguw7YY2")


def call_aliexpress_api(api_method, business_params):
  timestamp = str(int(time.time() * 1000))

  # Paramètres de base de la requête
  params = {
      "app_key": APP_KEY,
      "timestamp": timestamp,
      "sign_method": "sha256",
      "method": api_method,
      "partner_id": "sdk-python-2.0",
      "format": "json",
  }

  if ACCESS_TOKEN:
    params["access_token"] = ACCESS_TOKEN

  # Intégration des paramètres métier
  params.update(business_params)

  # --- Calcul de la signature standard AliExpress ---
  # Tri des clés par ordre alphabétique
  sorted_keys = sorted(params.keys())
  query_string = "".join(f"{k}{params[k]}" for k in sorted_keys)
  sign_str = APP_SECRET + query_string + APP_SECRET

  sign = (
      hmac.new(
          APP_SECRET.encode("utf-8"),
          sign_str.encode("utf-8"),
          hashlib.sha256,
      )
      .hexdigest()
      .upper()
  )

  params["sign"] = sign

  try:
    # Envoi en tant que formulaire (application/x-www-form-urlencoded)
    response = requests.post(GATEWAY_URL, data=params)
    return response.json()
  except Exception as e:
    print(f"Erreur de connexion : {e}")
    return None


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

  # Paramètres de recherche
  payload = {
      "keywords": "smartphone accessories",
      "page_no": "1",
      "page_size": "10",
  }

  response_data = call_aliexpress_api("aliexpress.ds.product.get", payload)

  print("Réponse reçue d'AliExpress :")
  print(json.dumps(response_data, indent=4))

  if response_data:
    print("Envoi des données vers le Google Sheet...")
    send_to_google_sheet(response_data)
