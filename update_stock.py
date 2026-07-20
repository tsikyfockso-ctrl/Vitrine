import requests
import json

# Remplacez cette URL par l'URL de votre application web Google Apps Script (celle de votre déploiement)
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbyOxZJjlRvmrw2U-al4CZa8ZsW4FsWwRkH9cMvRig84qqpwr0rp3lsnfpnjGjOAl8Xm/exec"

nouveau_produit = {
    "nom": "Produit Automatisé Mayah",
    "prix": "29.99",
    "img": "https://url-image.jpg"
}

try:
    response = requests.post(WEB_APP_URL, json=nouveau_produit)
    print("Réponse de Google :", response.text)
    print("Stock mis à jour avec succès via Apps Script !")
except Exception as e:
    print(f"Erreur : {e}")
    exit(1)
