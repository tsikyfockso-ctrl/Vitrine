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
            
            print(f"📦 {len(links)} produits détectés. Analyse des variantes en cours...")
            success_count = 0
            
            # Visite individuelle de chaque fiche produit
            for index, product_url in enumerate(links[:5], start=1): # Limité à 5 pour les tests, modifiable selon besoin
                print(f"\n🔍 [Produit {index}] Visite de la fiche : {product_url}")
                detail_page = context.new_page()
                
                try:
                    detail_page.goto(product_url, timeout=60000, wait_until="domcontentloaded")
                    human_delay(4, 6)
                    
                    # Scroll humain pour charger toutes les sections
                    detail_page.mouse.wheel(0, 500)
                    human_delay(2, 3)
                    
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
                    
                    # 2. Extraction de l'IMAGE principale
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
                    
                    # 3. Extraction LARGE des DÉTAILS
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
                            return null;
                        }""")
                        if extracted_details:
                            details = extracted_details[:400]
                    except Exception:
                        pass
                    
                    # 4. GESTION DES VARIANTES DE TAILLES (Basée sur votre structure sku-item--text--hYfAukP)
                    variants_data = []
                    
                    try:
                        # Recherche des boutons de tailles/SKU avec la structure exacte fournie
                        size_elements = detail_page.locator(".sku-item--text--hYfAukP").all()
                        
                        if len(size_elements) > 0:
                            print(f"   📏 {len(size_elements)} options de tailles détectées. Analyse variante par variante...")
                            
                            for s_elem in size_elements:
                                try:
                                    # Récupérer le nom de la taille (ex: XXL(US 14), M(US 6), etc.)
                                    size_name = s_elem.inner_text().strip()
                                    if not size_name:
                                        size_name = s_elem.get_attribute("title") or "Taille"
                                    
                                    # Cliquer de façon humaine sur l'option de taille pour actualiser la page
                                    s_elem.click()
                                    human_delay(1.5, 2.5) # Attente indispensable pour que le prix/stock s'actualisent
                                    
                                    # Extraire le prix mis à jour pour cette taille spécifique
                                    current_price = detail_page.evaluate("""() => {
                                        const pEl = document.querySelector('[class*="price-default--current"], [class*="current--F8OlYIo"], [class*="price--current"]');
                                        return pEl ? pEl.innerText.trim() : "0.00";
                                    }""")
                                    
                                    # Extraire le stock mis à jour pour cette taille spécifique
                                    current_stock = detail_page.evaluate("""() => {
                                        const stockEl = document.querySelector('[class*="quantity--info"], [class*="stock"]');
                                        if (stockEl && stockEl.innerText.trim()) {
                                            return stockEl.innerText.trim().replace(/\\n/g, ' ');
                                        }
                                        return "En stock";
                                    }""")
                                    
                                    variants_data.append(f"[{size_name} -> Prix: {current_price} | Stock: {current_stock}]")
                                    print(f"      🔹 Taille : {size_name} | Prix : {current_price} | Stock : {current_stock}")
                                    
                                except Exception as var_err:
                                    continue
                        else:
                            # S'il n'y a pas de variantes de tailles multiples, on récupère le prix et stock uniques globaux
                            single_price = detail_page.evaluate("""() => {
                                const pEl = document.querySelector('[class*="price-default--current"], [class*="current--F8OlYIo"]');
                                return pEl ? pEl.innerText.trim() : "0.00";
                            }""")
                            single_stock = detail_page.evaluate("""() => {
                                const stockEl = document.querySelector('[class*="quantity--info"], [class*="stock"]');
                                return stockEl ? stockEl.innerText.trim().replace(/\\n/g, ' ') : "En stock";
                            }""")
                            variants_data.append(f"[Taille unique -> Prix: {single_price} | Stock: {single_stock}]")
                            
                    except Exception as e:
                        print(f"   ⚠️ Erreur lors de l'analyse des tailles : {e}")
                        variants_data.append("[Variantes non disponibles]")
                    
                    # Concaténation de toutes les variantes de prix/stocks pour les envoyer proprement
                    final_pricing_details = " // ".join(variants_data)
                    
                    # Construction du Payload final pour votre Google Sheet
                    payload = {
                        "nom": title[:120],
                        "prix": final_pricing_details[:300], # Contient l'ensemble des prix par taille
                        "img": img_url,
                        "details": details,
                        "stock": "Voir détails des tailles"
                    }
                    
                    print(f"   ✔️ Nom : {title[:40]}...")
                    print(f"   ✔️ Envoi groupé des prix par taille vers Google Sheet...")
                    
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
                    human_delay(2, 4)
                    
            print(f"\n🎉 Terminé ! {success_count} produits avec toutes leurs variantes de prix par taille enregistrés.")
            
        except Exception as e:
            print(f"❌ Erreur critique globale : {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    scrape_and_send_to_sheet()
