import os
import requests

GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SCRIPT_URL")

def update_all_products_details_from_sheet():
    """
    Récupère la liste des produits depuis le Google Sheet (via doGet),
    puis génère et met à jour les détails et le stock pour chaque produit trouvé.
    """
    if not GOOGLE_SCRIPT_URL:
        print("Erreur : La variable d'environnement GOOGLE_SCRIPT_URL n'est pas définie.")
        return

    try:
        print("Récupération de la liste des produits depuis Google Sheets...")
        response = requests.get(GOOGLE_SCRIPT_URL, timeout=15)
        
        if response.status_code != 200:
            print(f"Erreur lors de la lecture du Sheet : Statut {response.status_code}")
            return
            
        produits = response.json()
        if not produits or not isinstance(produits, list):
            print("Aucun produit trouvé dans le Google Sheet.")
            return

        print(f"{len(produits)} produits trouvés. Génération des détails et du stock...")

        success_count = 0
        for p in produits:
            nom_produit = p.get("nom")
            if not nom_produit:
                continue

            # Génération dynamique des détails et du stock selon le nom du produit
            details_generes = f"Article de haute qualité : {nom_produit}. Parfait pour sublimer votre style au quotidien."
            stock_generes = "En stock (20 unités)"

            payload = {
                "nom": nom_produit,
                "details": details_generes,
                "stock": stock_generes
            }

            # Envoi de la mise à jour pour ce produit spécifique
            update_res = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=10)
            if update_res.status_code == 200:
                success_count += 1
                print(f"[{success_count}] Détails & stock mis à jour pour : {nom_produit[:30]}...")

        print(f"Mise à jour groupée terminée ! {success_count} produits mis à jour avec succès.")

    except Exception as e:
        print(f"Erreur critique lors de la mise à jour des détails : {e}")

if __name__ == "__main__":
    update_all_products_details_from_sheet()
