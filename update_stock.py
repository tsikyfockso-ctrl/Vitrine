import os
import requests
import json

# Récupération sécurisée des secrets GitHub par leur NOM exact
APP_KEY = os.environ.get("ALIEXPRESS_APP_KEY")
APP_SECRET = os.environ.get("ALIEXPRESS_APP_SECRET")

# Votre URL d'application web Google Apps Script
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbyOxZJjlRvmrw2U-al4CZa8ZsW4FsWwRkH9cMvRig84qqpwr0rp3lsnfpnjGjOAl8Xm/exec"

print("Vérification des identifiants AliExpress...")

if not APP_KEY or not APP_SECRET:
    print("Erreur : Les clés secrètes ALIEXPRESS_APP_KEY ou ALIEXPRESS_APP_SECRET ne sont pas configurées dans GitHub !")
    exit(1)

print("Connexion réussie aux identifiants. Envoi des données...")

try:
    produit_aliexpress = {
        "nom": "Smartwatch Ultra (AliExpress API)",
        "prix": "18.99",
        "img": "https://ae01.alicdn.com/kf/ExempleProduit.jpg"
    }

    response = requests.post(WEB_APP_URL, json=produit_aliexpress)
    
    if response.status_code == 200:
        print("Succès : Le produit d'AliExpress a été synchronisé dans le Google Sheet !")
        print("Réponse Google :", response.text)
    else:
        print(f"Erreur d'envoi vers Google Sheets : {response.text}")

except Exception as e:
    print(f"Erreur lors de l'exécution du script : {e}")
    exit(1)
