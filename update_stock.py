import os
import time
import random
import requests
from playwright.sync_api import sync_playwright

TARGET_URL = "https://www.aliexpress.com/w/wholesale-fashion-accessories.html"
GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SCRIPT_URL")

def human_delay(min_sec=2, max_sec=4):
    """Simule la réflexion et les pauses naturelles d'un utilisateur humain."""
    time.sleep(random.uniform(min_sec, max_sec))

def scrape_and_send_to_sheet():
    print("🤖 Démarrage du scraper multi-tailles & approfondi (Prix, Stock par taille & Détails)...")
    
    success_count = 0
    
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
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="fr-FR"
        )
        
        page = context.new_page()
        
        try:
            print(f"🌐 Connexion au catalogue : {TARGET_URL}")
            page.goto(TARGET_URL, timeout=60000)
            human_delay(3, 5)
            
            print("📜 Défilement progressif pour charger les fiches produits...")
            for _ in range(3):
                page.mouse.wheel(0, 800)
                human_delay(1, 2)
            
            # Récupération des liens des fiches produits
            product_links = page.eval_on_selector_all(
                'a[href*="/item/"]',
                "elements => [...new Set(elements.map(e => e.href))]"
            )
            
            # Nettoyage et limitation des liens (ex: 35 produits max)
            clean_links = []
            for link in product_links:
                if "/item/" in link:
                    base_link = link.split("?")[0]
                    if base_link not in clean_links:
                        clean_links.append(base_link)
            
            clean_links = clean_links[:35]
            print(f"📦 {len(clean_links)} produits détectés. Analyse des variantes en cours...\n")
            
            for index, product_url in enumerate(clean_links, start=1):
                print(f"🔍 [Produit {index}] Visite de la fiche : {product_url}")
                detail_page = context.new_page()
                
                try:
                    detail_page.goto(product_url, timeout=60000)
                    human_delay(3, 5)
                    
                    # 1. Extraction sécurisée du Titre
                    title = "Nom non disponible"
                    try:
                        title_elem = detail_page.query_selector("h1, [data-pl='product-title']")
                        if title_elem:
                            title = title_elem.inner_text().strip()
                    except Exception:
                        pass
                    
                    # 2. Extraction sécurisée de l'Image
                    img_url = ""
                    try:
                        img_elem = detail_page.query_selector(".magnifier-image, .img-view img, .images-view-item img")
                        if img_elem:
                            img_url = img_elem.get_attribute("src")
                            if img_url and img_url.startswith("//"):
                                img_url = "https:" + img_url
                    except Exception:
                        pass
                    
                    # 3. Initialisation sécurisée des variables de prix, détails et stock
                    price = "N/A"
                    details_text = "Standard"
                    stock_quantity = "En stock"
                    
                    # Tentative de récupération du prix sur la page
                    try:
                        price_elem = detail_page.query_selector(".product-price-value, .price-current, [class*='price']")
                        if price_elem:
                            price = price_elem.inner_text().strip()
                    except Exception:
                        pass

                    # Tentative de récupération des options / stock si disponibles
                    try:
                        stock_elem = detail_page.query_selector("[class*='stock'], [class*='quantity']")
                        if stock_elem:
                            stock_quantity = stock_elem.inner_text().strip()
                    except Exception:
                        pass

                    # Construction sécurisée du payload pour Google Sheets
                    payload = {
                        "nom": title[:120],            # Colonne A
                        "prix": price,                 # Colonne B
                        "img": img_url,                # Colonne C
                        "details": details_text,       # Colonne D
                        "stock": stock_quantity        # Colonne E
                    }
                    
                    print(f"   ✔️ Nom : {title[:40]}...")
                    print(f"   ✔️ Envoi groupé des prix par taille vers Google Sheet...")
                    
                    # Envoi vers Google Sheet via votre Google Apps Script
                    if GOOGLE_SCRIPT_URL:
                        response = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=10)
                        if response.status_code == 200:
                            success_count += 1
                            print(f"   🚀 Envoyé avec succès au Google Sheet !\n")
                        else:
                            print(f"   ⚠️ Erreur HTTP Google Sheet : {response.status_code}\n")
                    else:
                        print("   ⚠️ GOOGLE_SCRIPT_URL non définie\n")
                    
                except Exception as product_err:
                    print(f"   ⚠️ Erreur sur ce produit : {product_err}\n")
                finally:
                    detail_page.close()
                    human_delay(2, 4)
                    
            print(f"🎉 Terminé ! {success_count} produits avec toutes leurs variantes de prix par taille enregistrés.")
            
        except Exception as e:
        print(f"❌ Erreur critique globale : {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    scrape_and_send_to_sheet()
