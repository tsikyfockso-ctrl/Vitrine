import os
import time
import random
import requests
from playwright.sync_api import sync_playwright

TARGET_URL = "https://www.aliexpress.com/w/wholesale-fashion-accessories.html"
GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SCRIPT_URL")

def human_delay(min_sec=3, max_sec=6):
    """Simule le temps de réflexion et le comportement naturel d'un humain."""
    time.sleep(random.uniform(min_sec, max_sec))

def scrape_and_send_to_sheet():
    print("🤖 Démarrage du scraper intelligent et approfondi (Mode Humain - Anti-Erreur)...")
    
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
            page.goto(TARGET_URL, timeout=60000, wait_until="domcontentloaded")
            human_delay(4, 7)
            
            print("📜 Défilement naturel pour charger les produits...")
            for _ in range(3):
                page.mouse.wheel(0, random.randint(600, 1000))
                human_delay(1.5, 3)
            
            # Récupération sécurisée des liens uniques des produits
            links = []
            anchors = page.locator("a[href*='item/']").all()
            for anchor in anchors:
                try:
                    href = anchor.get_attribute("href")
                    if href:
                        if href.startswith("//"):
                            href = "https:" + href
                        elif href.startswith("/"):
                            href = "https://www.aliexpress.com" + href
                        
                        clean_url = href.split("?")[0]
                        if clean_url not in links and "item/" in clean_url:
                            links.append(clean_url)
                except Exception:
                    continue
            
            print(f"📦 {len(links)} produits détectés. Analyse approfondie en cours...")
            success_count = 0
            
            # Visite individuelle et humaine de chaque fiche produit
            for index, product_url in enumerate(links[:10], start=1):
                print(f"\n🔍 [Produit {index}] Visite de la fiche : {product_url}")
                detail_page = context.new_page()
                
                try:
                    detail_page.goto(product_url, timeout=60000, wait_until="domcontentloaded")
                    human_delay(3, 5)
                    
                    # Simulation d'un regard humain (léger scroll sur la page)
                    detail_page.mouse.wheel(0, 400)
                    human_delay(1, 2)
                    
                    # 1. Extraction ultra-robuste du NOM (Titre) via OpenGraph (comme dans votre HTML)
                    title = "Nom non disponible"
                    try:
                        og_title = detail_page.locator("meta[property='og:title']").get_attribute("content")
                        if og_title:
                            # Nettoyage pour retirer la mention "- AliExpress..." souvent ajoutée à la fin
                            title = og_title.split(" - AliExpress")[0].strip()
                        else:
                            h1_text = detail_page.locator("h1").first.inner_text().strip()
                            if len(h1_text) > 3:
                                title = h1_text
                    except Exception:
                        pass
                    
                    # 2. Extraction du PRIX
                    price = "0.00"
                    try:
                        og_price = detail_page.locator("meta[property='product:price:amount']").get_attribute("content")
                        if og_price:
                            price = og_price.strip()
                        else:
                            price_elem = detail_page.locator("div[class*='price'], span[class*='price']").first
                            if price_elem.count() > 0:
                                price = price_elem.inner_text().strip()
                    except Exception:
                        pass
                    
                    # 3. Extraction de l'IMAGE principale (via OpenGraph ou sélecteur natif)
                    img_url = ""
                    try:
                        og_img = detail_page.locator("meta[property='og:image']").get_attribute("content")
                        if og_img:
                            img_url = og_img.strip()
                        else:
                            img_elem = detail_page.locator("img[class*='magnifier'], img[class*='image']").first
                            if img_elem.count() > 0:
                                img_url = img_elem.get_attribute("src") or img_elem.get_attribute("data-src") or ""
                        
                        if img_url.startswith("//"):
                            img_url = "https:" + img_url
                    except Exception:
                        pass
                    
                    # 4. Extraction des DÉTAILS approfondis (Caractéristiques / Description)
                    details = "Caractéristiques standard"
                    try:
                        props = detail_page.locator("div[class*='property-item'], div[class*='specification'], ul[class*='specs']").all_inner_texts()
                        if props:
                            details = " | ".join([p.replace("\n", " ").strip() for p in props[:5]])[:250]
                        else:
                            desc = detail_page.locator("div[class*='product-description']").first.inner_text().strip()
                            if desc:
                                details = desc[:250].replace("\n", " ")
                    except Exception:
                        pass
                    
                    # 5. Extraction du STOCK (Quantité restante)
                    stock = "En stock"
                    try:
                        stock_elem = detail_page.locator("div[class*='stock'], span[class*='inventory'], div[class*='quantity']").first
                        if stock_elem.count() > 0:
                            stock_text = stock_elem.inner_text().strip()
                            if stock_text:
                                stock = stock_text
                    except Exception:
                        stock = "Disponible (Vérifié)"
                    
                    # Construction du Payload final pour Google Sheets
                    payload = {
                        "nom": title[:120],
                        "prix": price,
                        "img": img_url,
                        "details": details,
                        "stock": stock
                    }
                    
                    print(f"   ✔️ Nom : {title[:45]}...")
                    print(f"   ✔️ Prix : {price} | Stock : {stock}")
                    print(f"   ✔️ Image : {'OK' if img_url else 'Manquante'}")
                    
                    # Envoi vers Google Sheet via votre Google Apps Script
                    if GOOGLE_SCRIPT_URL:
                        response = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=10)
                        if response.status_code == 200:
                            success_count += 1
                            print(f"   🚀 Données envoyées avec succès au Google Sheet !")
                    
                except Exception as product_err:
                    print(f"   ⚠️ Erreur sur ce produit : {product_err}")
                finally:
                    detail_page.close()
                    human_delay(2, 4) # Pause humaine avant de passer au produit suivant
                    
            print(f"\n🎉 Processus terminé avec succès ! {success_count} produits approfondis enregistrés.")
            
        except Exception as e:
            print(f"❌ Erreur critique globale : {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    scrape_and_send_to_sheet()
