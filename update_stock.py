from bs4 import BeautifulSoup
import requests
import json

# URL de votre Web App Google Apps Script
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyOxZJjlRvmrw2U-al4CZa8ZsW4FsWwRkH9cMvRig84qqpwr0rp3lsnfpnjGjOAl8Xm/exec"

def analyser_html_cj(chemin_html):
    print("🤖 Analyse du fichier HTML CJ Dropshipping...")
    
    with open(chemin_html, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    
    # 1. Extraction du Nom
    title_tag = soup.find("title")
    nom_produit = title_tag.text.replace(" - CJdropshipping", "").strip() if title_tag else "Produit sans nom"
    
    # 2. Extraction de la description et des variantes (Couleurs / Tailles)
    desc_tag = soup.find("meta", attrs={"name": "description"})
    desc_text = desc_tag["content"] if desc_tag else ""
    
    # Exemple de contenu description : "... Color: Oatmeal, Red, Size: 36, 37, 38, 39, 40"
    couleurs = "Standard"
    tailles = "Unique"
    
    if "Color:" in desc_text:
        partie_couleur = desc_text.split("Color:")[1].split(", Size:")[0].strip()
        couleurs = partie_couleur
        
    if "Size:" in desc_text:
        tailles = desc_text.split("Size:")[1].strip()

    # 3. Extraction de l'image (via OpenGraph ou balises meta)
    img_tag = soup.find("meta", property="og:image")
    img_url = img_tag["content"] if img_tag else ""

    # 4. Construction des données selon la structure de votre Google Sheet (BDD_Mayah_Store)
    # Colonnes : nom, taille, prix par tailles, img par couleur, details, nombre de stock disponible
    donnees_produit = {
        "nom": nom_produit,
        "taille": tailles,
        "prix_par_tailles": "Voir fournisseur", # Ajustable selon vos prix extraits
        "img_par_couleur": img_url,
        "details": f"Couleurs: {couleurs}",
        "nombre_de_stock_disponible": "En stock"
    }
    
    return donnees_produit

def envoyer_vers_google_sheet(data):
    print("🚀 Envoi des données vers Google Sheet...")
    try:
        response = requests.post(GOOGLE_SCRIPT_URL, json=data)
        if response.status_code == 200:
            print("✅ Données envoyées avec succès !")
        else:
            print(f"⚠️ Erreur lors de l'envoi : {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur de connexion : {e}")

if __name__ == "__main__":
    # Nom du fichier HTML local fourni
    produit_data = analyser_html_cj("CJ dropshipping.html")
    print("Données extraites :", produit_data)
    envoyer_vers_google_sheet(produit_data)
