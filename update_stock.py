import os
import requests
from playwright.sync_api import sync_playwright

TARGET_URL = "https://www.aliexpress.com/w/wholesale-woman-fashion-accessories.html"
GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SCRIPT_URL")

def scrape_and_send_to_sheet():
    print("Démarrage de l'extraction (Nom, Prix, Image)...")
    
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
            print(f"Connexion à l'URL : {TARGET_URL}")
            page.goto(TARGET_URL, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(5000)
            
            print("Défilement de la page pour charger les produits...")
            for _ in range(3):
                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(2000)
                
            # Localisation des cartes produits sur AliExpress
            products = page.locator('.search-item-card-wrapper-wrap, [class*="product-card"]').all()
            print(f"Nombre de cartes produits trouvées : {len(products)}")
            
            success_count = 0
            for i, item in enumerate(products[:20]): # Limité aux 20 premiers produits
                try:
                    # Extraction du titre
                    title_elem = item.locator('h1, [class*="title"], [class*="multi--title"]').first
                    title = title_elem.inner_text().strip() if title_elem.count() > 0 else f"Produit Mayah {i+1}"
                    
                    # Extraction du prix
                    price_elem = item.locator('[class*="price"], [class*="current"]').first
                    price = price_elem.inner_text().strip() if price_elem.count() > 0 else "Prix sur demande"
                    
                    # Extraction de l'image
                    img_elem = item.locator('img').first
                    img_url = ""
                    if img_elem.count() > 0:
                        img_url = img_elem.get_attribute("src") or img_elem.get_attribute("data-src") or ""
                        
                    if img_url.startswith("//"):
                        img_url = "https:" + img_url
                        
                    if not title or not img_url:
                        continue
                        
                    # Construction du payload (Nom, Prix, Image)
                    payload = {
                        "nom": title[:120],
                        "prix": price,
                        "img": img_url
                    }
                    
                    # Envoi vers Google Sheets via Apps Script
                    if GOOGLE_SCRIPT_URL:
                        response = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=10)
                        if response.status_code == 200:
                            success_count += 1
                            print(f"[{success_count}] OK : {title[:25]}... | Enregistré (Nom, Prix, Image)")
                            
                except Exception as inner_err:
                    continue
                    
            print(f"Synchronisation terminée ! {success_count} produits synchronisés avec succès.")
            
        except Exception as e:
            print(f"Erreur critique durant l'exécution : {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    scrape_and_send_to_sheet()
