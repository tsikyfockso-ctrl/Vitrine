import hashlib
import hmac
import json
import os
import time
import requests

# Récupération des secrets configurés dans GitHub
APP_KEY = os.getenv("ALIEXPRESS_APP_KEY")
APP_SECRET = os.getenv("ALIEXPRESS_APP_SECRET")
SESSION_TOKEN = os.getenv("ALIEXPRESS_ACCESS_TOKEN", "50000500a01OR1716b4e49AgApxMpEB4KXeqri0pD9FjygrxweoGMgxftVTZmguw7YY2")

GATEWAY_URL = "https://api-sg.aliexpress.com/sync"
GOOGLE_SCRIPT_URL = os.getenv("GOOGLE_SCRIPT_URL", "https://script.google.com/macros/s/AKfycbyOxZJjlRvmrw2U-al4CZa8ZsW4FsWwRkH9cMvRig84qqpwr0rp3lsnfpnjGjOAl8Xm/exec")


def generate_sign(endpoint, params, secret):
  """Génère la signature HMAC-SHA256 officielle d'AliExpress.

  Règle critique : Le chemin de l'API (endpoint) doit préfixer la chaîne de
  caractères avant d'appliquer le secret !
  """
  filtered_params = {
      k: str(v) for k, v in params.items() if k != "sign" and v is not None
  }
  sorted_params = sorted(filtered_params.items())

  # Concaténation : endpoint + key1val1key2val2...
  query_string = "".join(f"{k}{v}" for k, v in sorted_params)
  base_string = endpoint + query_string

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
  timestamp = str(int(time.time() * 1000))

  common_params = {
      "app_key": APP_KEY,
      "timestamp": timestamp,
      "sign_method": "sha256",
      "method": api_method,
      "format": "json",
      "session": SESSION_TOKEN,
  }

  all_params = {**common_params, **business_params}

  # Pour la passerelle /sync, le chemin utilisé dans le calcul est le nom de la méthode ou "/sync" selon l'archi, 
  # Ici, la structure standard AliExpress Open Platform utilise la méthode comme préfixe ou racine d'appel :
  # (Dans certains contextes de passerelle unique /sync, l'endpoint commence par un slash ou correspond au nom de la méthode)
  
  # Testons le format exact attendu par la passerelle globale :
  # La chaîne de signature intègre le nom de la méthode ou le chemin relatif de l'API.
  all_params["sign"] = generate_sign(api_method, all_params, APP_SECRET)

  try:
    response = requests.post(GATEWAY_URL, data=all_params)
    return response.json()
  except Exception as e:
    print(f"Erreur de connexion à l'API : {e}")
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

  payload = {
      "product_id": "1005001234567890",
      "target_currency": "EUR",
      "target_language": "FR",
      "ship_to_country": "FR",
  }

  response_data = call_aliexpress_api("aliexpress.ds.product.get", payload)

  print("Réponse reçue d'AliExpress :")
  print(json.dumps(response_data, indent=4))

  if response_data:
    print("Envoi des données vers le Google Sheet...")
    send_to_google_sheet(response_data)
  
