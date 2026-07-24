import os
import requests
from playwright.sync_api import sync_playwright

TARGET_URL = "https://www.aliexpress.com/w/wholesale-fashion-accessories.html"
GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SCRIPT_URL")

def scrape_and_send_to_sheet():
    print("Démarrage de l'extraction complète (Nom, Prix, Image, Stock, Détails)...")
    
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
            
            print("Défilement progressif pour charger les produits...")
            for _ in range(3):
                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(2000)
            
            # Récupération des liens des produits depuis la page de liste
            # (Ajustez le sélecteur selon la structure actuelle d'AliExpress)
            product_links = page.eval_on_selector_all(
                'a[href*="/item/"]', 
                "elements => [...new Set(elements.map(e => e.href))] "
            )
            
            # Limiter à un nombre raisonnable pour le test (ex: les 10 premiers)
            product_links = product_links[:10]
            print(f" {len(product_links)} produits trouvés. Extraction des détails individuels...")
            
            success_count = 0
            
            for index, link in enumerate(product_links):
                try:
                    # Ouvrir la page spécifique du produit
                    detail_page = context.new_page()
                    detail_page.goto(link, timeout=45000, wait_until="domcontentloaded")
                    detail_page.wait_for_timeout(3000)
                    
                    # 1. Extraction du Nom
                    title = "Nom non trouvé"
                    title_elem = detail_page.query_selector('h1') or detail_page.query_selector('[class*="title"]')
                    if title_elem:
                        title = title_elem.inner_text().strip()
                    
                    # 2. Extraction du Prix
                    price = "Prix non trouvé"
                    price_elem = detail_page.query_selector('[class*="price--current"]') or detail_page.query_selector('[class*="price"]')
                    if price_elem:
                        price = price_elem.inner_text().strip()
                    
                    # 3. Extraction de l'Image principale
                    img_url = ""
                    img_elem = detail_page.query_selector('img[class*="magnifier"], img[class*="image"], .pdp-info-img img')
                    if img_elem:
                        img_url = img_elem.get_attribute("src") or img_elem.get_attribute("nitro-lazy-src")
                        
                    if img_url:
                        if img_url.startswith("//"):
                            img_url = "https:" + img_url
                        elif img_url.startswith("/"):
                            img_url = "https://www.aliexpress.com" + img_url
                    
                    # 4. Extraction du Stock (quantité disponible)
                    stock_qty = "Stock non spécifié"
                    stock_elem = detail_page.query_selector('[class*="quantity"], [class*="inventory"], [class*="stock"]')
                    if stock_elem:
                        stock_qty = stock_elem.inner_text().strip()
                        
                    # 5. Extraction des Détails / Description
                    details = ""
                    desc_elem = detail_page.query_selector('#product-description, [class*="description"]')
                    if desc_elem:
                        details = desc_elem.inner_text().strip()[:400] # Limité pour la BDD
                        
                    detail_page.close()
                    
                    # Validation et envoi du payload complet vers Google Sheets
                    if not img_url or "data:image" in img_url or "http" not in img_url:
                        continue
                        
                    payload = {
                        "nom": title[:120],
                        "prix": price,
                        "img": img_url,
                        "stock": stock_qty,
                        "details": details
                    }
                    
                    if GOOGLE_SCRIPT_URL:
                        response = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=10)
                        if response.status_code == 200:
                            success_count += 1
                            print(f"[{success_count}] OK : {title[:25]}... | Prix: {price} | Stock: {stock_qty}")
                            
                except Exception as inner_err:
                    print(f"Erreur sur un produit : {inner_err}")
                    continue
                    
            print(f"Synchronisation terminée ! {success_count} produits complets mis à jour.")
            
        except Exception as e:
            print(f"Erreur critique durant l'exécution : {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    scrape_and_send_to_sheet()
