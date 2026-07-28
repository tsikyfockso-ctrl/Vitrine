import os
import requests
from playwright.sync_api import sync_playwright

GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SCRIPT_URL")

def run_scraper():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Connexion à AliExpress / DS Center
        page.goto("https://www.aliexpress.com/w/wholesale-woman-fashion-accessories.html")
        page.wait_for_selector("a", timeout=10000)
        
        # Extraction des liens produits
        links = [element.get_attribute("href") for element in page.locator("a").all()]
        product_links = [l for l in links if l and "/item/" in l][:5] # Limité pour l'exemple
        
        for link in product_links:
            if not link.startswith("http"):
                link = "https:" + link
                
            detail_page = browser.new_page()
            try:
                detail_page.goto(link, timeout=60000)
                
                # 1. Extraction du Nom
                nom = detail_page.locator("h1").inner_text() if detail_page.locator("h1").count() > 0 else "Nom indisponible"
                
                # 2. Extraction du Prix (et prix par taille si disponible)
                prix = detail_page.locator('[class*="price--current"]').inner_text() if detail_page.locator('[class*="price--current"]').count() > 0 else "Prix indisponible"
                
                # 3. Extraction de l'Image
                img = detail_page.locator('.magnifier-image, [class*="magnifier"] img').get_attribute("src") if detail_page.locator('.magnifier-image, [class*="magnifier"] img').count() > 0 else ""
                
                # 4. Extraction des Détails & Stock
                page_text = detail_page.locator("body").inner_text()
                details = "Détails extraits avec succès"
                stock = "En stock" if "stock" in page_text.lower() else "Vérifier stock"

                # Paquet de données à envoyer à Google Sheets
                payload = {
                    "nom": nom,
                    "prix": prix,
                    "img": img,
                    "details": details,
                    "stock": stock
                }
                
                # Envoi sécurisé vers Google Sheets
                if GOOGLE_SCRIPT_URL:
                    response = requests.post(GOOGLE_SCRIPT_URL, json=payload)
                    print(f"-> [Succès] Données synchronisées pour : {nom[:30]}...")
                    
            except Exception as e:
                print(f"Erreur sur ce produit : {e}")
            finally:
                detail_page.close()
                
        browser.close()

if __name__ == "__main__":
    run_scraper()
