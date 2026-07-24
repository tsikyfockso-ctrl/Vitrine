import os
import requests
from playwright.sync_api import sync_playwright

TARGET_URL = "https://www.aliexpress.com/w/wholesale-best-seller.html"
GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SCRIPT_URL")

def scrape_and_send_to_sheet():
    print("Démarrage de l'extraction automatique du catalogue global AliExpress...")
    
    with sync_playwright() as p:
        # Lancement avec un mode standard et des arguments anti-détection
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        
        try:
            print("Connexion à la page AliExpress...")
            page.goto(TARGET_URL, timeout=60000, wait_until="domcontentloaded")
            
            # Au lieu d'attendre un sélecteur strict qui bloque, on attend juste un court instant que le corps de page charge
            page.wait_for_timeout(5000)
            
            print("Défilement de la page pour charger les éléments...")
            for _ in range(5):
                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(2000)
                
            # Utilisation d'un sélecteur générique basé sur les liens d'articles (beaucoup plus stable)
            product_cards = page.locator("a[href*='/item/']")
            count = product_cards.count()
            print(f"{count} liens de produits détectés sur la page.")
            
            success_count = 0
            seen_urls = set()
            
            for i in range(min(count, 30)): # Limite aux 30 premiers produits par exécution pour éviter les timeouts
                card = product_cards.nth(i)
                
                try:
                    # Récupération du lien pour identifier le produit
                    href = card.get_attribute("href")
                    if not href or href in seen_urls:
                        continue
                    seen_urls.add(href)
                    
                    # Recherche du texte (titre) et du prix à l'intérieur ou à proximité de l'élément
                    text_content = card.inner_text().split('\n')
                    
                    title = "Titre indisponible"
                    price = "Prix indisponible"
                    
                    # Analyse intelligente du texte récupéré dans la carte
                    for line in text_content:
                        if len(line.strip()) > 15 and title == "Titre indisponible":
                            title = line.strip()
                        elif "US $" in line or "€" in line or "USD" in line:
                            price = line.strip()
                            
                    # Extraction de l'image associée
                    img_element = card.locator("img").first
                    img_url = ""
                    if img_element.count() > 0:
                        img_url = img_element.get_attribute("src") or img_element.get_attribute("data-src") or ""
                        if img_url.startswith("//"):
                            img_url = "https:" + img_url
                            
                    payload = {
                        "nom": title[:100],  # Sécurité sur la longueur
                        "prix": price,
                        "img": img_url
                    }
                    
                    if GOOGLE_SCRIPT_URL:
                        response = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=10)
                        if response.status_code == 200:
                            success_count += 1
                            print(f"Produit synchronisé : {title[:30]}... ({price})")
                            
                except Exception as inner_e:
                    continue
                    
            print(f"Synchronisation terminée ! {success_count} produits envoyés avec succès dans BDD_Mayah_Store.")
            
        except Exception as e:
            print(f"Erreur critique durant l'exécution du scraping : {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    scrape_and_send_to_sheet()
