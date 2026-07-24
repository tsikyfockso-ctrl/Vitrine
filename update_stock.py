import os
import requests
from playwright.sync_api import sync_playwright

# On utilise une recherche ciblée par mot-clé au lieu d'une page globale pour éviter les blocages de sécurité
TARGET_URL = "https://www.aliexpress.com/w/wholesale-fashion-accessories.html"
GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SCRIPT_URL")

def scrape_and_send_to_sheet():
    print("Démarrage de l'extraction sécurisée AliExpress...")
    
    with sync_playwright() as p:
        # Lancement avec des options pour paraître totalement humain
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
            
            # Petite pause humaine pour laisser le contenu s'injecter en JS
            page.wait_for_timeout(6000)
            
            # Simulation d'un défilement lent et humain
            print("Défilement intelligent de la page...")
            for i in range(4):
                page.mouse.wheel(0, 800)
                page.wait_for_timeout(2000)
                
            # Recherche élargie des éléments de produits (liens contenant /item/)
            product_cards = page.locator("a[href*='/item/']")
            count = product_cards.count()
            print(f"Succès : {count} éléments produits trouvés.")
            
            success_count = 0
            seen_urls = set()
            
            # On limite aux 25 premiers produits pour un traitement rapide et propre
            for i in range(min(count, 25)):
                card = product_cards.nth(i)
                
                try:
                    href = card.get_attribute("href")
                    if not href or href in seen_urls:
                        continue
                    seen_urls.add(href)
                    
                    text_content = card.inner_text().split('\n')
                    title = "Titre indisponible"
                    price = "Prix indisponible"
                    
                    for line in text_content:
                        clean_line = line.strip()
                        if len(clean_line) > 12 and title == "Titre indisponible" and "US $" not in clean_line:
                            title = clean_line
                        elif "US $" in clean_line or "€" in clean_line or "USD" in clean_line:
                            price = clean_line
                            
                    # Récupération de l'image
                    img_element = card.locator("img").first
                    img_url = ""
                    if img_element.count() > 0:
                        img_url = img_element.get_attribute("src") or img_element.get_attribute("data-src") or ""
                        if img_url.startswith("//"):
                            img_url = "https:" + img_url
                            
                    # On ignore les éléments vides ou invalides
                    if title == "Titre indisponible" or not img_url:
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
                            print(f"[{success_count}] Envoyé : {title[:35]}... ({price})")
                            
                except Exception as inner_err:
                    continue
                    
            print(f"Synchronisation terminée avec succès ! {success_count} produits ajoutés dans BDD_Mayah_Store.")
            
        except Exception as e:
            print(f"Erreur critique durant l'exécution : {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    scrape_and_send_to_sheet()
