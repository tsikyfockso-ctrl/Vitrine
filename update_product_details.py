import os
import re
import requests
from playwright.sync_api import sync_playwright

TARGET_URL = "https://www.aliexpress.com/w/wholesale-woman-fashion-accessories.html"
GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SCRIPT_URL")

def update_details_and_stock():
    print("Démarrage de la mise à jour ciblée (Détails et Stock réels)...")
    
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
            
            # Défilement pour charger les liens
            for _ in range(2):
                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(2000)
                
            product_links = page.locator('a[href*="item"]').evaluate_all(
                'elements => Array.from(new Set(elements.map(e => e.href))).filter(href => href.includes("/item/"))'
            )
            
            print(f"Nombre de liens produits trouvés : {len(product_links)}")
            success_count = 0
            
            # On traite les premiers produits de la liste
            for i, link in enumerate(product_links[:10]):
                detail_page = context.new_page()
                try:
                    print(f"[{i+1}] Analyse de la fiche : {link}")
                    detail_page.goto(link, timeout=45000, wait_until="domcontentloaded")
                    detail_page.wait_for_timeout(3000)
                    
                    # On récupère le nom pour identifier le produit à mettre à jour
                    title_elem = detail_page.locator('h1, [class*="product-title"], [class*="title--wrap"]').first
                    title = title_elem.inner_text().strip() if title_elem.count() > 0 else f"Produit {i+1}"
                    
                    # 1. Extraction des VRAIS DÉTAILS
                    specs_container = detail_page.locator('[class*="product-property"], [class*="specification"], [class*="property-item"]').all_inner_texts()
                    if specs_container:
                        nouveaux_details = " | ".join([spec.replace("\n", " ") for spec in specs_container[:5]])
                    else:
                        nouveaux_details = f"Détails officiels pour : {title}"
                        
                    # 2. Extraction du VRAI STOCK RÉEL
                    page_text = detail_page.inner_text()
                    nouveau_stock = "En stock"
                    
                    stock_match = re.search(r'(\d+)\s*(?:pieces available|pièces disponibles|items left|restants)', page_text, re.IGNORECASE)
                    if stock_match:
                        nouveau_stock = f"⚠️ {stock_match.group(0)}"
                    elif "out of stock" in page_text.lower() or "épuisé" in page_text.lower():
                        nouveau_stock = "Rupture de stock"
                    else:
                        nouveau_stock = "En stock (Disponible)"

                    # Payload ciblé pour les colonnes Details et Stock
                    payload = {
                        "nom": title[:120],
                        "details": nouveaux_details[:300],  # Colonne D -> Details
                        "stock": nouveau_stock             # Colonne E -> Stock
                    }
                    
                    if GOOGLE_SCRIPT_URL:
                        response = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=15)
                        if response.status_code == 200:
                            success_count += 1
                            print(f" -> [Mis à jour] Détails et Stock enregistrés pour : {title[:30]}...")
                            
                except Exception as inner_err:
                    print(f"Erreur sur ce produit : {inner_err}")
                finally:
                    detail_page.close()
                    
            print(f"Mise à jour ciblée terminée ! {success_count} produits actualisés.")
            
        except Exception as e:
            print(f"Erreur critique : {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    update_details_and_stock()
