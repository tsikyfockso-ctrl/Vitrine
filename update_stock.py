import os
import requests
from playwright.sync_api import sync_playwright

# URL globale des meilleures ventes / tendances pour récupérer un maximum de produits
TARGET_URL = "https://www.aliexpress.com/w/wholesale-best-seller.html"

# Récupération sécurisée de l'URL de votre Google Apps Script depuis les secrets GitHub
GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SCRIPT_URL")

def scrape_and_send_to_sheet():
    print("Démarrage de l'extraction automatique du catalogue global AliExpress...")
    
    with sync_playwright() as p:
        # Lancement du navigateur en arrière-plan
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Simulation d'un utilisateur réel pour éviter les blocages de sécurité
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        
        try:
            # Navigation vers la page cible
            page.goto(TARGET_URL, timeout=60000)
            
            # Attente que les premiers blocs de produits s'affichent
            page.wait_for_selector(".multi--outWrapper--Se3e0jK", timeout=15000)
            
            # Défilement progressif vers le bas de la page (plusieurs fois) 
            # pour forcer AliExpress à charger un maximum de produits dynamiquement
            print("Chargement dynamique des produits en cours (scroll)...")
            for _ in range(6):
                page.mouse.wheel(0, 1500)
                page.wait_for_timeout(2500)
                
            # Sélection de toutes les cartes produits visibles sur la page
            product_cards = page.locator(".multi--outWrapper--Se3e0jK")
            count = product_cards.count()
            print(f"{count} produits détectés et prêts à être synchronisés.")
            
            success_count = 0
            for i in range(count):
                card = product_cards.nth(i)
                
                # Extraction sécurisée du nom
                try:
                    title = card.locator("h3, [class*='title']").inner_text()
                except:
                    title = "Titre indisponible"
                    
                # Extraction sécurisée du prix
                try:
                    price = card.locator("[class*='price--current'], [class*='price']").first.inner_text()
                except:
                    price = "Prix indisponible"
                    
                # Extraction sécurisée de l'image
                try:
                    img_element = card.locator("img")
                    img_url = img_element.get_attribute("src") or img_element.get_attribute("data-src")
                    if img_url and img_url.startswith("//"):
                        img_url = "https:" + img_url
                except:
                    img_url = ""
                    
                # Format JSON respectant exactement votre Google Apps Script (nom, prix, img)
                payload = {
                    "nom": title,
                    "prix": price,
                    "img": img_url
                }
                
                # Envoi automatique vers votre Google Sheet 'BDD_Mayah_Store'
                if GOOGLE_SCRIPT_URL:
                    try:
                        response = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=10)
                        if response.status_code == 200:
                            success_count += 1
                    except Exception as req_err:
                        print(f"Erreur réseau pour le produit {i+1}: {req_err}")
                else:
                    print("Attention : URL Google Script manquante dans les variables d'environnement.")
                    
            print(f"Synchronisation terminée ! {success_count} sur {count} produits envoyés avec succès dans BDD_Mayah_Store.")
            
        except Exception as e:
            print(f"Erreur critique durant l'exécution du scraping : {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    scrape_and_send_to_sheet()
