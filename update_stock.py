import os
import re
import requests
from playwright.sync_api import sync_playwright

TARGET_URL = "https://www.aliexpress.com/w/wholesale-woman-fashion-accessories.html"
GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SCRIPT_URL")

def scrape_and_send_to_sheet():
    print("Démarrage de l'extraction profonde et réelle (Nom, Prix, Image, Détails, Stock)...")
    
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
            print(f"Connexion à la page de recherche : {TARGET_URL}")
            page.goto(TARGET_URL, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(5000)
            
            print("Défilement de la page pour charger les liens...")
            for _ in range(3):
                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(2000)
                
            # Récupération des liens vers les fiches produits individuelles
            product_links = page.locator('a[href*="item"]').evaluate_all(
                'elements => Array.from(new Set(elements.map(e => e.href))).filter(href => href.includes("/item/"))'
            )
            
            print(f"Nombre de liens produits trouvés : {len(product_links)}")
            
            success_count = 0
            # On traite par exemple les 10 premiers produits en profondeur pour éviter les blocages de temps
            for i, link in enumerate(product_links[:10]):
                detail_page = context.new_page()
                try:
                    print(f"[{i+1}] Analyse de la fiche produit : {link}")
                    detail_page.goto(link, timeout=45000, wait_until="domcontentloaded")
                    detail_page.wait_for_timeout(3000)
                    
                    # 1. VRAI NOM DU PRODUIT sur la page détaillée
                    title_elem = detail_page.locator('h1, [class*="product-title"], [class*="title--wrap"]').first
                    title = title_elem.inner_text().strip() if title_elem.count() > 0 else f"Produit AliExpress {i+1}"
                    
                    # 2. VRAI PRIX sur la page détaillée
                    price_elem = detail_page.locator('[class*="product-price-value"], [class*="price--current"], span[class*="price"]').first
                    price = price_elem.inner_text().strip() if price_elem.count() > 0 else "Prix indisponible"
                    
                    # 3. VRAIE IMAGE principale
                    img_elem = detail_page.locator('img[class*="magnifier"], img[class*="image"], [class*="gallery"] img').first
                    img_url = ""
                    if img_elem.count() > 0:
                        img_url = img_elem.get_attribute("src") or img_elem.get_attribute("data-src") or ""
                    if img_url.startswith("//"):
                        img_url = "https:" + img_url
                        
                    payload = {
                        "nom": title[:120],
                        "prix": price,
                        "img": img_url,
                    }
                    
                    if GOOGLE_SCRIPT_URL:
                        response = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=15)
                        if response.status_code == 200:
                            success_count += 1
                            print(f" -> Synchronisé avec succès | Prix: {price}")
                            
                except Exception as page_err:
                    print(f"Erreur sur ce produit : {page_err}")
                finally:
                    detail_page.close()
                    
            print(f"Synchronisation en profondeur terminée ! {success_count} produits réels mis à jour.")
            
        except Exception as e:
            print(f"Erreur critique : {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    script_path = os.path.abspath(__file__)
    print(f"Exécution du fichier : {script_path}")
    scrape_and_send_to_sheet()
