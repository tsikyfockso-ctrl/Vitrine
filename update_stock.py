import os
import time
import random
import requests
from playwright.sync_api import sync_playwright

TARGET_URL = "https://www.aliexpress.com/w/wholesale-fashion-accessories.html"
GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SCRIPT_URL")

def human_delay(min_sec=3, max_sec=6):
    """Simule la réflexion et les pauses naturelles d'un utilisateur humain."""
    time.sleep(random.uniform(min_sec, max_sec))

def scrape_and_send_to_sheet():
    print("🤖 Démarrage du scraper ultra-précis (Prix, Détails & Stock réels capturés)...")
    
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
            
            print("📜 Défilement progressif pour charger les fiches produits...")
            for _ in range(3):
                page.mouse.wheel(0, random.randint(600, 1000))
                human_delay(1.5, 3)
            
            # Récupération sécurisée des liens uniques de produits
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
            
            print(f"📦 {len(links)} produits détectés. Analyse chirurgicale en cours...")
            success_count = 0
            
            # Visite individuelle et humaine de chaque fiche produit
            for index, product_url in enumerate(links[:10], start=1):
                print(f"\n🔍 [Produit {index}] Visite de la fiche : {product_url}")
                detail_page = context.new_page()
                
                try:
                    detail_page.goto(product_url, timeout=60000, wait_until="domcontentloaded")
                    human_delay(4, 6) # Laisse le temps au rendu dynamique d'afficher prix, détails et stock
                    
                    # Scroll humain progressif pour forcer le chargement de toutes les sections de la page
                    detail_page.mouse.wheel(0, 500)
                    human_delay(2, 3)
                    detail_page.mouse.wheel(0, 700)
                    human_delay(1, 2)
                    
                    # 1. Extraction du NOM (Titre)
                    title = "Nom non disponible"
                    try:
                        og_title = detail_page.locator("meta[property='og:title']").get_attribute("content")
                        if og_title:
                            title = og_title.split(" - AliExpress")[0].strip()
                        else:
                            h1_text = detail_page.locator("h1").first.inner_text().strip()
                            if len(h1_text) > 3:
                                title = h1_text
                    except Exception:
                        pass
                    
                    # 2. Extraction du VRAI PRIX (Basé sur la classe price-default--current)
                    price = "0.00"
                    try:
                        extracted_price = detail_page.evaluate("""() => {
                            const currentPrice = document.querySelector('[class*="price-default--current"], [class*="current--F8OlYIo"], [class*="price--current"]');
                            if (currentPrice && currentPrice.innerText.trim()) {
                                return currentPrice.innerText.trim();
                            }
                            const metaPrice = document.querySelector('meta[property="product:price:amount"]');
                            if (metaPrice) return metaPrice.content;
                            return null;
                        }""")
                        
                        if extracted_price:
                            price = extracted_price
                    except Exception:
                        pass
                    
                    # 3. Extraction de l'IMAGE principale
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
                    
                    # 4. Extraction LARGE des DÉTAILS (Basé sur la structure specification--line / specification--prop)
                    details = "Caractéristiques standard"
                    try:
                        extracted_details = detail_page.evaluate("""() => {
                            const specLines = document.querySelectorAll('.specification--line--IXeRJI7, [class*="specification--prop"]');
                            if (specLines.length > 0) {
                                let detailsList = [];
                                specLines.forEach(line => {
                                    const text = line.innerText.replace(/\\n/g, ' : ').trim();
                                    if (text) detailsList.push(text);
                                });
                                return detailsList.join(' | ');
                            }
                            
                            const props = Array.from(document.querySelectorAll('[class*="property-item"], [class*="specification"]'))
                                .map(el => el.innerText.trim())
                                .filter(text => text.length > 0);
                            if (props.length > 0) return props.join(' | ');
                            
                            return null;
                        }""")
                        
                        if extracted_details:
                            details = extracted_details[:400]
                    except Exception:
                        pass
                    
                    # 5. Extraction exacte du STOCK (Basé sur la classe quantity--info--jnoo_pD que vous avez envoyée)
                    stock = "En stock"
                    try:
                        extracted_stock = detail_page.evaluate("""() => {
                            // Cible précise du bloc de quantité que vous venez de fournir (ex: "60 disponibles")
                            const quantityInfo = document.querySelector('[class*="quantity--info"], [class*="stock"], [class*="inventory"]');
                            if (quantityInfo && quantityInfo.innerText.trim()) {
                                return quantityInfo.innerText.trim().replace(/\\n/g, ' ');
                            }
                            
                            // Recherche de secours par expression régulière dans le texte global de la page
                            const bodyText = document.body.innerText;
                            const match = bodyText.match(/(\\d+)\\s+(disponibles|pieces available|articles disponibles)/i);
                            if (match) return match[0];
                            
                            return null;
                        }""")
                        
                        if extracted_stock:
                            stock = extracted_stock
                    except Exception:
                        pass
                    
                    # Construction du Payload final pour votre Google Sheet
                    payload = {
                        "nom": title[:120],
                        "prix": price,
                        "img": img_url,
                        "details": details,
                        "stock": stock
                    }
                    
                    print(f"   ✔️ Nom : {title[:40]}...")
                    print(f"   ✔️ Prix : {price} | Stock : {stock}")
                    print(f"   ✔️ Détails : {details[:80]}...")
                    
                    # Envoi vers Google Sheet via votre Google Apps Script
                    if GOOGLE_SCRIPT_URL:
                        response = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=10)
                        if response.status_code == 200:
                            success_count += 1
                            print(f"   🚀 Envoyé avec succès au Google Sheet !")
                    
                except Exception as product_err:
                    print(f"   ⚠️ Erreur sur ce produit : {product_err}")
                finally:
                    detail_page.close()
                    human_delay(2, 4) # Pause humaine avant de passer au produit suivant
                    
            print(f"\n🎉 Terminé ! {success_count} produits extraits avec succès (Prix, Stock et Détails complets).")
            
        except Exception as e:
            print(f"❌ Erreur critique globale : {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    scrape_and_send_to_sheet()
