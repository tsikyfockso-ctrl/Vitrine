import os
import re
import requests
from playwright.sync_api import sync_playwright

TARGET_URL = "https://www.aliexpress.com/w/wholesale-woman-fashion-accessories.html"
GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SCRIPT_URL")

def scrape_and_sync_all():
    print("Démarrage de l'extraction globale (Nom, Prix, Image, Détails, Stock)...")
    
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
                
            product_links = page.locator('a[href*="item"]').evaluate_all(
                'elements => Array.from(new Set(elements.map(e => e.href))).filter(href => href.includes("/item/"))'
            )
            
            print(f"Nombre de liens produits trouvés : {len(product_links)}")
            success_count = 0
            
            for i, link in enumerate(product_links[:10]):
                detail_page = context.new_page()
                try:
                    print(f"[{i+1}/10] Analyse complète : {link}")
                    detail_page.goto(link, timeout=45000, wait_until="domcontentloaded")
                    detail_page.wait_for_timeout(4000) # Attente un peu plus longue pour charger le rendu dynamique
                    
                    page_text = detail_page.locator("body").inner_text()
                    
                    # 1. Nom précis du produit (Ciblage strict du H1 AliExpress)
                    title_elem = detail_page.locator('h1[data-pl="product-title"], h1.title--wrap--1Z_BhZm, h1').first
                    title = title_elem.inner_text().strip() if title_elem.count() > 0 else f"Produit AliExpress {i+1}"
                    
                    # Nettoyage si le titre récupère des artefacts parasites
                    title = re.sub(r'\s+', ' ', title)
                    
                    # 2. Prix précis
                    price_elem = detail_page.locator('[class*="price--current"], [class*="product-price-value"]').first
                    price = price_elem.inner_text().strip() if price_elem.count() > 0 else "Prix indisponible"
                    
                    # 3. Image principale
                    img_elem = detail_page.locator('.magnifier-image, img[class*="magnifier"], [class*="gallery"] img, .images-view-item img').first
                    img_url = ""
                    if img_elem.count() > 0:
                        img_url = img_elem.get_attribute("src") or img_elem.get_attribute("data-src") or ""
                    if img_url.startswith("//"):
                        img_url = "https:" + img_url
                        
                    # 4. Détails / Caractéristiques
                    specs_container = detail_page.locator('[class*="product-property"], [class*="specification"], [class*="property-item"]').all_inner_texts()
                    if specs_container:
                        nouveaux_details = " | ".join([spec.replace("\n", " ") for spec in specs_container[:5]])
                    else:
                        nouveaux_details = f"Caractéristiques officielles : {title[:50]}"
                        
                    # 5. Stock (Recherche ciblée dans les blocs d'inventaire ou le texte global)
                    nouveau_stock = "En stock"
                    stock_elem = detail_page.locator('[class*="sku-stock"], [class*="inventory"], [class*="quantity"]').first
                    
                    if stock_elem.count() > 0:
                        stock_text = stock_elem.inner_text().strip()
                        if stock_text:
                            nouveau_stock = stock_text
                    
                    # Fallback par regex si l'élément spécifique n'est pas trouvé
                    if "En stock" in nouveau_stock or not nouveau_stock:
                        stock_match = re.search(r'(\d+)\s*(?:pieces available|pièces disponibles|items left|restants|disponibles)', page_text, re.IGNORECASE)
                        if stock_match:
                            nouveau_stock = f"{stock_match.group(1)} pièces disponibles"
                        elif "out of stock" in page_text.lower() or "épuisé" in page_text.lower():
                            nouveau_stock = "Rupture de stock"
                        else:
                            nouveau_stock = "En stock (Disponible)"

                    # Payload unique prêt pour Google Sheets
                    payload = {
                        "nom": title[:120],
                        "prix": price,
                        "img": img_url,
                        "details": nouveaux_details[:300],
                        "stock": nouveau_stock
                    }
                    
                    print(f" -> Données extraites : Nom={title[:30]}... | Prix={price} | Stock={nouveau_stock}")
                    
                    if GOOGLE_SCRIPT_URL:
                        response = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=15)
                        if response.status_code == 200:
                            success_count += 1
                            print(f" -> [Succès] Synchronisé avec Google Sheets.")
                            
                except Exception as inner_err:
                    print(f"Erreur sur ce produit : {inner_err}")
                finally:
                    detail_page.close()
                    
            print(f"Synchronisation globale terminée ! {success_count} produits mis à jour correctement.")
            
        except Exception as e:
            print(f"Erreur critique : {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    scrape_and_sync_all()
