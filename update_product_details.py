import os
import requests

GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SCRIPT_URL")

def update_single_product_details(nom_produit, nouveaux_details, nouveau_stock):
    """
    Envoie une requête pour mettre à jour uniquement les colonnes Details et Stock
    pour un produit spécifique dans le Google Sheet.
    """
    if not GOOGLE_SCRIPT_URL:
        print("Erreur : La variable d'environnement GOOGLE_SCRIPT_URL n'est pas définie.")
        return

    payload = {
        "nom": nom_produit,
        "details": nouveaux_details,  # Colonne D
        "stock": nouveau_stock        # Colonne E
    }

    try:
        print(f"Mise à jour des détails et du stock pour : {nom_produit}...")
        response = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"Succès ! Le produit '{nom_produit}' a été mis à jour dans le Google Sheet.")
        else:
            print(f"Erreur du serveur Google : Statut {response.status_code}")
            
    except Exception as e:
        print(f"Erreur lors de la communication avec Google Apps Script : {e}")

if __name__ == "__main__":
    # Exemple d'utilisation du script de mise à jour ciblée
    produit_cible = "Exemple de collier tendance"
    details_mis_a_jour = "Matière : Alliage de zinc résistant, design élégant et moderne."
    stock_mis_a_jour = "En stock (8 unités)"
    
    update_single_product_details(produit_cible, details_mis_a_jour, stock_mis_a_jour)
