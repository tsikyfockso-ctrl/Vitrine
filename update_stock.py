import os
import re
import requests
from playwright.sync_api import sync_playwright

TARGET_URL = "https://www.aliexpress.com/w/wholesale-woman-fashion-accessories.html"
GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SCRIPT_URL")

def scrape_and_sync_all():
    print("Démarrage de l'extraction globale corrigée (Nom réel, Prix, Image, Détails réels, Stock)...")
    
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
            
            print("Attente du chargement des éléments produits...")
            page.wait_for_selector('a[href*="item"]', timeout=15000)
            page.wait_for_timeout(3000)
            
            print("Défilement de la page pour charger les liens...")
            for _ in range(4):
                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(2000)
                
            product_links = page.locator('a').evaluate_all(
                'elements => Array.from(new Set(elements.map(e => e.href))).filter(href => href && (href.includes("/item/") || href.includes("aliexpress.us/item/") || href.includes("aliexpress.com/item/")))'
            )
            
            print(f"Nombre de liens produits trouvés : {len(product_links)}")
            success_count = 0
            
            for i, link in enumerate(product_links[:10]):
                detail_page = context.new_page()
                try:
                    print(f"[{i+1}/10] Analyse approfondie : {link}")
                    detail_page.goto(link, timeout=45000, wait_until="domcontentloaded")
                    detail_page.wait_for_timeout(5000) # Laisser le temps au JS d'AliExpress d'injecter le contenu
                    
                    # 1. Extraction robuste du VRAI Nom du produit (titre de la page ou balise h1)
                    title = ""
                    h1_elem = detail_page.locator('h1').first
                    if h1_elem.count() > 0:
                        title = h1_elem.inner_text().strip()
                    
                    if not title or len(title) < 3:
                        title = detail_page.title() # Utiliser le titre de l'onglet si le h1 échoue
                        
                    title = re.sub(r'\s+', ' ', title).replace(" - AliExpress", "").strip()
                    if not title:
                        title = f"Produit Mode Accessoire {i+1}"

                    # 2. Extraction robuste du Prix
                    price = "Prix indisponible"
                    price_selectors = [
                        '.product-price-value', 
                        '[class*="price--current"]', 
                        '[class*="price-view"]', 
                        '.es--price--F50K9wW',
                        'span[class*="price"]'
                    ]
                    for sel in price_selectors:
                        p_elem = detail_page.locator(sel).first
                        if p_elem.count() > 0:
                            p_text = p_elem.inner_text().strip()
                            if p_text and any(char.isdigit() for char in p_text):
                                price = p_text
                                break

                    # 3. Extraction robuste de l'Image principale
                    img_url = ""
                    img_selectors = [
                        '.magnifier-image', 
                        'img[class*="magnifier"]', 
                        '[class*="slider"] img', 
                        '[class*="gallery"] img',
                        'img'
                    ]
                    for sel in img_selectors:
                        img_elem = detail_page.locator(sel).first
                        if img_elem.count() > 0:
                            temp_url = img_elem.get_attribute("src") or img_elem.get_attribute("data-src") or ""
                            if temp_url and "alicdn" in temp_url:
                                img_url = temp_url
                                break
                    if img_url.startswith("//"):
                        img_url = "https:" + img_url

                    # 4. Extraction robuste des Détails (caractéristiques du produit)
                    details_list = []
                    props_elems = detail_page.locator('[class*="product-property"], [class*="specification"], [class*="property-item"], [class*="item--content"]').all_inner_texts()
                    for prop in props_elems:
                        cleaned = prop.replace("\n", " ").strip()
                        if cleaned and len(cleaned) < 100:
                            details_list.append(cleaned)
                    
                    if details_list:
                        nouveaux_details = " | ".join(details_list[:5])
                    else:
                        nouveaux_details = f"Article de mode de haute qualité - Ref: {i+1}"

                    # 5. Extraction robuste du Stock
                    page_text = detail_page.locator("body").inner_text()
                    nouveau_stock = "En stock"
                    
                    stock_match = re.search(r'(\d+)\s*(?:pieces available|pièces disponibles|items left|restants|disponibles)', page_text, re.IGNORECASE)
                    if stock_match:
                        nouveau_stock = f"{stock_match.group(1)} pièces disponibles"
                    elif "out of stock" in page_text.lower() or "épuisé" in page_text.lower() or "rupture" in page_text.lower():
                        nouveau_stock = "Rupture de stock"
                    else:
                        nouveau_stock = "En stock (Disponible)"

                    # Payload complet contenant toutes les colonnes à envoyer au Google Script
                    payload = {
                        "nom": title[:120],
                        "prix": price,
                        "img": img_url,
                        "details": nouveaux_details[:300],
                        "stock": nouveau_stock
                    }
                    
                    print(f" -> Vrai Nom : {title[:40]}... | Prix : {price} | Stock : {nouveau_stock}")
                    
                    if GOOGLE_SCRIPT_URL:
                        response = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=15)
                        if response.status_code == 200:
                            success_count += 1
                            print(f" -> [Succès] Ligne mise à jour dans Google Sheets.")
                            
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
