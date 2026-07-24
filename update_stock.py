import os
import requests
from playwright.sync_api import sync_playwright

TARGET_URL = "https://www.aliexpress.com/w/wholesale-fashion-accessories.html"
GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SCRIPT_URL")

def scrape_and_send_to_sheet():
    print("Démarrage de l'extraction multi-sélecteurs AliExpress...")
    
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
            print(f"Connexion à l'URL : {TARGET_URL}")
            page.goto(TARGET_URL, timeout=60000, wait_until="domcontentloaded")
            
            page.wait_for_timeout(5000)
            
            print("Défilement progressif pour charger les images et les blocs...")
            for i in range(5):
                page.mouse.wheel(0, 800)
                page.wait_for_timeout(2000)
                
            # Utilisation d'un sélecteur large et flexible qui cible toutes les cartes de produits possibles sur AliExpress
            product_cards = page.locator("div[class*='search-card-item'], div[class*='manhattan--container'], a[href*='item']")
            count = product_cards.count()
            print(f"Succès : {count} éléments potentiels trouvés.")
            
            success_count = 0
            seen_titles = set()
            
            for i in range(min(count, 40)):
                card = product_cards.nth(i)
                
                try:
                    full_text = card.inner_text()
                    text_lines = full_text.split('\n')
                    
                    title = "Titre indisponible"
                    price = "Prix indisponible"
                    
                    for line in text_lines:
                        clean_line = line.strip()
                        if not clean_line:
                            continue
                        
                        if any(symbol in clean_line for symbol in ["US $", "€", "USD", "$", "US$"]) and price == "Prix indisponible":
                            price = clean_line
                        elif len(clean_line) > 12 and title == "Titre indisponible" and "US $" not in clean_line and "€" not in clean_line:
                            title = clean_line
                            
                    # Éviter les doublons basés sur le titre
                    if title in seen_titles or title == "Titre indisponible":
                        continue
                    seen_titles.add(title)
                            
                    # Extraction robuste de l'image
                    img_element = card.locator("img").first
                    img_url = ""
                    if img_element.count() > 0:
                        img_url = img_element.get_attribute("data-src") or img_element.get_attribute("src") or ""
                        if "data:image" in img_url or not img_url:
                            img_url = img_element.get_attribute("srcset") or ""
                            if img_url:
                                img_url = img_url.split(" ")[0]
                                
                    if img_url:
                        if img_url.startswith("//"):
                            img_url = "https:" + img_url
                        elif img_url.startswith("/"):
                            img_url = "https://www.aliexpress.com" + img_url
                    
                    if not img_url or "data:image" in img_url:
                        continue
                        
                    payload = {
                        "nom": title[:120],
                        "prix": price,
                        "img": img_url
                    }
                    
                    if GOOGLE_SCRIPT_URL:
                        response = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=10)
                        if response.status_code == 200:
                            success_count += 1
                            print(f"[{success_count}] Envoyé avec succès : {title[:25]}... | Prix : {price}")
                            
                except Exception as inner_err:
                    continue
                    
            print(f"Synchronisation terminée ! {success_count} produits ajoutés dans BDD_Mayah_Store.")
            
        except Exception as e:
            print(f"Erreur critique durant l'exécution : {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    scrape_and_send_to_sheet()
