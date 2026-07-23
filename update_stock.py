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
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyOxZJjlRvmrw2U-al4CZa8ZsW4FsWwRkH9cMvRig84qqpwr0rp3lsnfpnjGjOAl8Xm/exec"


def generate_sign(params, secret):
  """Génère la signature HMAC-SHA256 officielle d'AliExpress.

  Tous les paramètres (communs et spécifiques) doivent être inclus dans
  l'ordre alphabétique.
  """
  # Trie les paramètres par ordre alphabétique de leurs clés
  sorted_params = sorted(params.items())

  # Concatène le secret, puis tous les couples clé+valeur, puis à nouveau le secret
  query_string = "".join(f"{k}{v}" for k, v in sorted_params)
  base_string = secret + query_string + secret

  # Calcule le HMAC-SHA256 en majuscules
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
  """Exécute une requête sécurisée vers l'API AliExpress."""
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

  # Fusion de TOUS les paramètres (obligatoires + métier)
  all_params = {**common_params, **business_params}

  # Génération de la signature incluant l'ensemble des paramètres
  all_params["sign"] = generate_sign(all_params, APP_SECRET)

  try:
    response = requests.post(GATEWAY_URL, data=all_params)
    result = response.json()
    return result
  except Exception as e:
    print(f"Erreur de connexion à l'API AliExpress : {e}")
    return None


def send_to_google_sheet(data):
  if not GOOGLE_SCRIPT_URL or GOOGLE_SCRIPT_URL == "https://script.google.com/macros/s/AKfycbyOxZJjlRvmrw2U-al4CZa8ZsW4FsWwRkH9cMvRig84qqpwr0rp3lsnfpnjGjOAl8Xm/exec":
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
        " secrets GitHub."
    )
    exit(1)

  # Paramètres de recherche pour le dropshipping
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
