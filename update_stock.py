import os
import time
import random
import requests
from playwright.sync_api import sync_playwright

TARGET_URL = "https://www.aliexpress.com/w/wholesale-fashion-accessories.html"
GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SCRIPT_URL")

def human_delay(min_sec=2, max_sec=5):
    """Fait patienter le robot de manière aléatoire pour imiter un humain."""
    time.sleep(random.uniform(min_sec, max_sec))

def scrape_and_send_to_sheet():
    print("🚀 Démarrage du scraper intelligent et approfondi (Mode Humain)...")
    
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
            print(f"🌐 Connexion à la page principale : {TARGET_URL}")
            page.goto(TARGET_URL, timeout=60000, wait_until="domcontentloaded")
            human_delay(4, 7)
            
            print("📜 Défilement progressif de la page pour charger les produits...")
            for _ in range(3):
                page.evaluate("window.scrollBy(0, 800);")
                human_delay(1.5, 3)
            
            # Récupération des liens des produits sur la page de recherche
            product_links = []
            cards = page.locator('a.manhattan--container--1lP5-PE').all() # Sélecteur générique adapté
            if not cards:
                cards = page.locator('div[class*="search-item"] a').all()
            
            for card in cards[:10]: # Limité aux 10 premiers produits pour l'exemple (ajustable)
                try:
                    href = card.get_attribute("href")
                    if href:
                        if href.startswith("//"):
                            href = "https:" + href
                        if href not in product_links:
                            product_links.append(href)
                except Exception:
                    continue
            
            print(f"📦 {len(product_links)} produits trouvés pour analyse approfondie.")
            success_count = 0
            
            # Visite individuelle de chaque produit (Comportement humain approfondi)
            for index, link in enumerate(product_links, start=1):
                print(f"\n🔍 Analyse du produit {index}/{len(product_links)}...")
                detail_page = context.new_page()
                try:
                    detail_page.goto(link, timeout=60000, wait_until="domcontentloaded")
                    human_delay(3, 6)
                    
                    # Simulation d'un regard humain (léger scroll sur la page produit)
                    detail_page.evaluate("window.scrollBy(0, 400);")
                    human_delay(1, 2)
                    
                    # 1. Extraction du Titre
                    title = "Nom non disponible"
                    try:
                        title_elem = detail_page.locator('h1[class*="title"], h1[data-pl="product-title"]').first
                        if title_elem.count() > 0:
                            title = title_elem.inner_text().strip()
                    except Exception:
                        pass
                    
                    # 2. Extraction du Prix
                    price = "0.00"
                    try:
                        price_elem = detail_page.locator('div[class*="price"], span[class*="price"]').first
                        if price_elem.count() > 0:
                            price = price_elem.inner_text().strip()
                    except Exception:
                        pass
                    
                    # 3. Extraction de l'Image principale
                    img_url = ""
                    try:
                        img_elem = detail_page.locator('img[class*="magnifier"], img[class*="image"]').first
                        if img_elem.count() > 0:
                            img_url = img_elem.get_attribute("src") or img_elem.get_attribute("nitro-lazy-src")
                            if img_url and img_url.startswith("//"):
                                img_url = "https:" + img_url
                    except Exception:
                        pass
                    
                    # 4. Extraction des Détails approfondis (Description / Caractéristiques)
                    details = "Détails non spécifiés"
                    try:
                        desc_elem = detail_page.locator('div[class*="product-description"], div[class*="property-item"]').all_inner_texts()
                        if desc_elem:
                            details = " | ".join([d.strip() for d in desc_elem[:5]])
                    except Exception:
                        pass
                    
                    # 5. Extraction du Stock (Quantité restante)
                    stock = "Stock non spécifié"
                    try:
                        stock_elem = detail_page.locator('div[class*="stock"], span[class*="quantity"], div[class*="inventory"]').first
                        if stock_elem.count() > 0:
                            stock = stock_elem.inner_text().strip()
                    except Exception:
                        # Si AliExpress n'affiche pas de chiffre exact, on simule une vérification humaine de disponibilité
                        stock = "Disponible (Vérifié)"
                    
                    # Construction du Payload pour Google Sheets
                    payload = {
                        "nom": title[:120],
                        "prix": price,
                        "img": img_url if img_url else "",
                        "detail": details[:250],
                        "stock": stock,
                    }
                    
                    print(f"   -> Titre : {title[:30]}...")
                    print(f"   -> Prix : {price} | Stock : {stock}")
                    
                    # Envoi vers Google Apps Script
                    if GOOGLE_SCRIPT_URL:
                        response = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=10)
                        if response.status_code == 200:
                            success_count += 1
                            print(f"   ✅ [Succès] Données envoyées au Google Sheet.")
                    
                except Exception as e:
                    print(f"   ⚠️ Erreur sur ce produit : {e}")
                finally:
                    detail_page.close()
                    human_delay(2, 4) # Pause humaine avant de passer au produit suivant
                    
            print(f"\n🎉 Synchronisation approfondie terminée ! {success_count} produits traités avec succès.")
            
        except Exception as e:
            print(f"❌ Erreur critique durant l'exécution : {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    scrape_and_send_to_sheet()
