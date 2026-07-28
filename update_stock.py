import os
import requests
from playwright.sync_api import sync_playwright

GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SCRIPT_URL")

def run_intelligent_robot():
    with sync_playwright() as p:
        # Lancement du navigateur en arrière-plan (mode headless)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("🔍 Connexion au DS Center / AliExpress...")
        # URL de recherche ou de votre espace DS Center cible
        page.goto("https://www.aliexpress.com/w/wholesale-dropshipping.html", timeout=60000)
        page.wait_for_selector("a", timeout=10000)
        
        # Récupération des liens de produits de la page
        links = [element.get_attribute("href") for element in page.locator("a").all()]
        product_links = [l for l in links if l and "/item/" in l][:5] # Limité aux 5 premiers pour test
        
        print(f"📦 {len(product_links)} produits détectés à analyser en profondeur.")

        for link in product_links:
            if not link.startswith("http"):
                link = "https:" + link
                
            detail_page = browser.new_page()
            try:
                print(f"🚀 Analyse intelligente du produit : {link}")
                detail_page.goto(link, timeout=60000)
                detail_page.wait_for_timeout(3000) # Laisser charger le contenu dynamique JavaScript
                
                # 1. Extraction intelligente du Nom
                nom = "Nom introuvable"
                for selector in ["h1", '[class*="title--wrap"]', '[class*="product-title"]']:
                    if detail_page.locator(selector).count() > 0:
                        nom = detail_page.locator(selector).first.inner_text().strip()
                        break
                
                # 2. Extraction du Prix Global de base
                prix = "Prix introuvable"
                for selector in ['[class*="price--current"]', '[class*="product-price"]', '.su-price']:
                    if detail_page.locator(selector).count() > 0:
                        prix = detail_page.locator(selector).first.inner_text().strip()
                        break

                # 3. Extraction intelligente des prix par TAILLE (Size)
                tailles_prix = {}
                size_buttons = detail_page.locator('[class*="sku-property-item"], [class*="sku-item"], [class*="size"] button, [class*="size"] span').all()
                
                if size_buttons:
                    print("   👕 Analyse des prix par taille...")
                    for btn in size_buttons[:6]: # Limité pour la performance
                        try:
                            size_name = btn.inner_text().strip()
                            btn.click()
                            detail_page.wait_for_timeout(1000)
                            current_size_price = detail_page.locator('[class*="price--current"]').first.inner_text().strip() if detail_page.locator('[class*="price--current"]').count() > 0 else prix
                            if size_name:
                                tailles_prix[size_name] = current_size_price
                        except Exception:
                            continue
                
                if tailles_prix:
                    details_taille_str = " | ".join([f"{size}: {p}" for size, p in tailles_prix.items()])
                else:
                    details_taille_str = "Taille unique / Standard"

                # 4. EXTRACTION DES DÉTAILS COMPLETS DU PRODUIT (Description & Spécifications)
                details_produit = "Détails non disponibles"
                desc_selectors = [
                    '[class*="product-description"]', 
                    '[class*="detail-desc"]', 
                    '#product-description', 
                    '[class*="description"]',
                    '.ui-box-body'
                ]
                for sel in desc_selectors:
                    if detail_page.locator(sel).count() > 0:
                        # On récupère le texte propre de la description
                        text_desc = detail_page.locator(sel).first.inner_text().strip()
                        if len(text_desc) > 20: # S'assurer qu'on a bien récupéré du contenu significatif
                            details_produit = text_desc.replace('\n', ' ')[:1000] # Limité à 1000 caractères pour Google Sheet
                            break

                # 5. Extraction de l'Image principale
                img = ""
                for img_sel in ['.magnifier-image', '[class*="magnifier"] img', '[class*="image-viewer"] img', 'img']:
                    if detail_page.locator(img_sel).count() > 0:
                        src = detail_page.locator(img_sel).first.get_attribute("src")
                        if src:
                            if src.startswith("//"):
                                img = "https:" + src
                            elif src.startswith("http"):
                                img = src
                            break

                # 6. Extraction du Stock / Quantité disponible
                page_text = detail_page.locator("body").inner_text().lower()
                stock = "En stock"
                if "rupture" in page_text or "épuisé" in page_text or "out of stock" in page_text:
                    stock = "Rupture de stock"
                elif "disponible" in page_text or "pièces" in page_text:
                    stock = "En stock (vérifié)"

                # Paquet de données unifié complet
                payload = {
                    "link": link,
                    "nom": nom,
                    "prix": prix,
                    "prix_par_taille": details_taille_str,
                    "details": details_produit,  # <--- Les détails complets du produit
                    "img": img,
                    "stock": stock
                }
                
                print(f"   ✅ Données prêtes pour : {nom[:30]}... (Stock: {stock})")

                # Envoi sécurisé vers Google Apps Script
                if GOOGLE_SCRIPT_URL:
                    res = requests.post(GOOGLE_SCRIPT_URL, json=payload)
                    if res.status_code == 200:
                        print("   ☁️ Synchronisé avec succès dans Google Sheets sans écrasement !")
                    else:
                        print(f"   ⚠️ Erreur Google Sheet : {res.status_code}")
                else:
                    print("   ⚠️ GOOGLE_SCRIPT_URL non configurée.")

            except Exception as e:
                print(f"   ❌ Erreur sur ce produit : {e}")
            finally:
                detail_page.close()
                
        browser.close()

if __name__ == "__main__":
    run_intelligent_robot()
