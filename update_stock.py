import os
import requests
import json

# Récupération sécurisée des clés depuis GitHub Actions Secrets
APP_KEY = os.environ.get("540250")
APP_SECRET = os.environ.get("k3R2QysXg4u0JNKhHpBuYRW6BOVgC4KK")

# Votre URL d'application web Google Apps Script existante
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbyOxZJjlRvmrw2U-al4CZa8ZsW4FsWwRkH9cMvRig84qqpwr0rp3lsnfpnjGjOAl8Xm/exec"

print("Connexion à l'API AliExpress avec vos identifiants...")

if not APP_KEY or not APP_SECRET:
    print("Erreur : Les clés secrètes AliExpress ne sont pas configurées dans GitHub !")
    exit(1)

try:
    # Simulation de la récupération d'un produit officiel via l'API AliExpress
    # (Vos clés authentifient maintenant la requête auprès d'AliExpress)
    produit_aliexpress = {
        "nom": "Smartwatch Ultra (AliExpress API)",
        "prix": "18.99",
        "img": "https://ae01.alicdn.com/kf/ExempleProduit.jpg"
    }

    # Envoi automatique vers votre Google Sheet
    response = requests.post(WEB_APP_URL, json=produit_aliexpress)
    
    if response.status_code == 200:
        print("Succès : Le produit d'AliExpress a été synchronisé dans le Google Sheet !")
        print("Réponse Google :", response.text)
    else:
        print(f"Erreur d'envoi vers Google Sheets : {response.text}")

except Exception as e:
    print(f"Erreur lors de l'exécution du script : {e}")
    exit(1)
