import os
import requests

GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SCRIPT_URL")

def update_all_products_details_from_sheet():
    if not GOOGLE_SCRIPT_URL:
        print("Erreur : La variable d'environnement GOOGLE_SCRIPT_URL n'est pas définie.")
        return

    try:
        print("Récupération de la liste des produits depuis Google Sheets...")
        # Augmentation du timeout à 30 secondes pour laisser le temps à Google Apps Script de répondre
        response = requests.get(GOOGLE_SCRIPT_URL, timeout=60)
        
        if response.status_code != 200:
            print(f"Erreur lors de la lecture du Sheet : Statut {response.status_code}")
            return
            
        produits = response.json()
        if not produits or not isinstance(produits, list):
            print("Aucun produit trouvé dans le Google Sheet.")
            return

        print(f"{len(produits)} produits trouvés. Mise à jour des détails et du stock...")

        success_count = 0
        for p in produits:
            nom_produit = p.get("nom")
            if not nom_produit:
                continue

            details_generes = f"Article de haute qualité : {nom_produit}. Design élégant et tendance."
            stock_generes = "En stock (15 unités)"

            payload = {
                "nom": nom_produit,
                "details": details_generes,
                "stock": stock_generes
            }

            try:
                update_res = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=15)
                if update_res.status_code == 200:
                    success_count += 1
                    print(f"[{success_count}] Mis à jour : {nom_produit[:25]}...")
            except requests.exceptions.Timeout:
                print(f"Timeout lors de la mise à jour pour : {nom_produit[:25]}...")
            except Exception as e:
                print(f"Erreur sur {nom_produit[:25]} : {e}")

        print(f"Mise à jour terminée ! {success_count} produits mis à jour.")

    except requests.exceptions.Timeout:
        print("Erreur critique : La requête GET vers Google Sheets a expiré (timeout).")
    except Exception as e:
        print(f"Erreur critique lors de la mise à jour des détails : {e}")

if __name__ == "__main__":
    update_all_products_details_from_sheet()
