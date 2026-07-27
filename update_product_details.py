import os
import requests
from playwright.sync_api import sync_playwright

# URL de votre Google Apps Script (utilisez la même ou une fonction dédiée pour la mise à jour)
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
            # 1. Vous pouvez récupérer la liste des produits depuis votre Google Sheet ou définir une liste d'URLs à tester
            # Exemple d'URL de test d'un produit individuel sur AliExpress :
            sample_product_url = "https://www.aliexpress.com/item/example.html" 
            
            print(f"Connexion à la page du produit : {sample_product_url}")
            page.goto(sample_product_url, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(4000)
            
            # 2. Extraction des détails approfondis (Description, Caractéristiques, etc.)
            # Les sélecteurs s'adaptent aux blocs de description standard d'AliExpress
            description = "Description indisponible"
            specifications = "Spécifications non fournies"
            
            try:
                # Tentative de récupération de la description détaillée ou des spécifications
                desc_element = page.locator("div[class*='product-description'], div[class*='detail-content']").first
                if desc_element.count() > 0:
                    description = desc_element.inner_text()[:500] # Limité à 500 caractères pour la base
            except Exception:
                pass

            try:
                specs_element = page.locator("div[class*='product-prop'], div[class*='specification']").first
                if specs_element.count() > 0:
                    specifications = specs_element.inner_text()[:300]
            except Exception:
                pass

            # 3. Préparation des données pour la BDD (Colonnes D et E)
            payload = {
                "action": "update_details", # Permet à votre Google Apps Script de savoir qu'il s'agit d'une mise à jour de colonnes D et E
                "nom": "Nom du produit cible", # Permet d'identifier la ligne correspondante dans le Sheet
                "description": description,     # Colonne D
                "specifications": specifications # Colonne E
            }
            
            # Envoi vers Google Sheets
            if GOOGLE_SCRIPT_URL:
                response = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=10)
                if response.status_code == 200:
                    print("Détails du produit mis à jour avec succès dans le Google Sheet (Colonnes D & E).")
                    
        except Exception as e:
            print(f"Erreur durant l'extraction des détails : {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    scrape_product_details()
