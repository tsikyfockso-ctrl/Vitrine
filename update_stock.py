import os
import requests

# Récupération des secrets depuis l'environnement GitHub Actions ou local
CJ_API_KEY = os.getenv("CJ_API_KEY", "")
GOOGLE_SCRIPT_URL = os.getenv("GOOGLE_SCRIPT_URL", "")

def get_cj_access_token():
    """
    Génère et récupère le jeton d'accès CJ Dropshipping de manière 100% sécurisée.
    Empêche tout retour de type booléen en cas d'erreur réseau ou d'API.
    """
    url = "https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "apiKey": CJ_API_KEY
    }
    
    print("🔑 Génération du jeton d'accès CJ Dropshipping...")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"📊 Code HTTP reçu de CJ (Auth) : {response.status_code}")
        
        # Vérification si la réponse est bien du JSON
        try:
            data = response.json()
        except ValueError:
            print(f"❌ Erreur : La réponse de CJ n'est pas du JSON valide. Texte brut : {response.text[:200]}")
            return None
            
        if not isinstance(data, dict):
            print(f"❌ Erreur : Format de réponse inattendu (pas un dictionnaire).")
            return None
            
        # Vérification du succès de l'API CJ
        if data.get("result") is True or data.get("code") == 200:
            # Selon la structure de l'API CJ, le token peut être dans data['data'] ou data['accessToken']
            token_data = data.get("data")
            if isinstance(token_data, dict):
                token = token_data.get("accessToken") or token_data.get("token")
            else:
                token = data.get("accessToken") or data.get("token")
                
            if token:
                print("🔑 Jeton d'accès généré avec succès !")
                return token
                
        print(f"⚠️ Message d'erreur API CJ : {data.get('message', 'Inconnu')}")
        return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur réseau lors de la connexion à l'API CJ : {e}")
        return None

def main():
    print("🤖 Démarrage de la synchronisation CJ Dropshipping -> Google Sheet...")
    
    if not CJ_API_KEY or CJ_API_KEY == "***":
        print("❌ Erreur : La clé API CJ_API_KEY est manquante ou invalide.")
        return

    # Étape 1 : Récupération du jeton sécurisé
    token = get_cj_access_token()
    
    if not token:
        print("❌ Impossible de démarrer la synchronisation sans jeton valide.")
        return

    print("🌐 Jeton valide récupéré. Prêt pour la synchronisation des produits...")
    # La suite de votre logique de recherche et d'envoi vers Google Sheet...

if __name__ == "__main__":
    main()
