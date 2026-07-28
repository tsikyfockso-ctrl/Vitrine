import os
import requests
from playwright.sync_api import sync_playwright

GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SCRIPT_URL")

def scrape_product_details():
    print("Démarrage du scraper de détails de produits...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-infobars",
                "--window-size=1920,1080"
            ]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="en-US"
        )
        
        page = context.new_page()
        
        try:
            # 1. Utilisation d'une vraie page de recherche pour récupérer des liens valides dynamiquement
            target_url = "https://www.aliexpress.com/w/wholesale-woman-fashion-accessories.html"
            print(f"Connexion à la page de catalogue : {target_url}")
            
            # Utilisation de 'commit' au lieu de 'domcontentloaded' pour aller plus vite et éviter les timeouts de scripts lourds
            page.goto(target_url, timeout=60000, wait_until="commit")
            page.wait_for_timeout(5000)
            
            # Récupération du premier lien de produit disponible sur la page
            product_links = page.locator("a[href*='/item/']").evaluate_all(
                "elements => elements.map(e => e.href).filter(href => href.includes('/item/'))"
            )
            
            if not product_links:
                print("Aucun lien de produit trouvé.")
                return

            # On prend un exemple concret parmi les produits trouvés
            real_product_url = product_links[0]
            print(f"Visite de la page du produit : {real_product_url}")
            
            page.goto(real_product_url, timeout=60000, wait_until="commit")
            page.wait_for_timeout(5000)
            
            # 2. Extraction des détails de la page produit
            description = "Description détaillée non disponible"
            specifications = "Spécifications standard"
            
            try:
                # Sélecteur ciblant le titre ou les blocs descriptifs de la page produit AliExpress
                title_elem = page.locator("h1").first
                if title_elem.count() > 0:
                    description = f"Produit officiel - {title_elem.inner_text()}"
            except Exception:
                pass

            # 3. Envoi des données vers Google Sheets (Colonnes D et E)
            payload = {
                "action": "update_details",
                "description": description[:300],     # Colonne D
                "specifications": specifications      # Colonne E
            }
            
            if GOOGLE_SCRIPT_URL:
                response = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=10)
                if response.status_code == 200:
                    print("Détails mis à jour avec succès dans le Google Sheet.")
                    
        except Exception as e:
            print(f"Erreur durant l'extraction des détails : {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    scrape_product_details()
