import os
import json
from deep_translator import GoogleTranslator
import iop  # Bibliothèque officielle Alibaba Open Platform

# Récupération des clés depuis les secrets GitHub
APP_KEY = os.environ.get("ALIBABA_APP_KEY", "504452")
APP_SECRET = os.environ.get("ALIBABA_APP_SECRET", "yJ6EZQfA529GJbpDxKqqoP61ww30JH0R")

MOTS_CLES_RECHERCHE = ["Women Dress", "Lady Dress", "Women clothing"]
# Passerelle officielle Alibaba Open Platform
ALIBABA_GATEWAY = "https://api.alibaba.com/router" 

def traduire_texte(texte):
    if not texte:
        return "Nom indisponible"
    try:
        trads = GoogleTranslator(source='auto', target='fr').translate(str(texte).strip())
        return trads if trads else texte
    except Exception:
        return texte

def recuperer_produits_alibaba_api(keyword):
    """
    Interroge l'API Alibaba en utilisant le client officiel iop (SDK Python)
    adapté aux routes /alibaba/icbu/...
    """
    client = iop.IopClient(ALIBABA_GATEWAY, APP_KEY, APP_SECRET)
    
    # Utilisation du chemin officiel de l'API de recherche/liste de produits ICBU
    request = iop.IopRequest('/alibaba/icbu/product/query/v2')
    
    # Ajout des paramètres de recherche
    request.add_api_param('keyword', keyword)
    request.add_api_param('pageSize', '50')
    request.add_api_param('pageNo', '1')

    try:
        response = client.execute(request)
        print(f"Type de réponse Alibaba : {getattr(response, 'type', 'N/A')}")
        
        if hasattr(response, 'body') and response.body:
            data = json.loads(response.body) if isinstance(response.body, str) else response.body
            # Extraction des produits selon la structure de retour standard Alibaba
            return data.get("result", {}).get("products", [])
    except Exception as e:
        print(f"⚠️ Erreur lors de la requête Alibaba pour '{keyword}' : {e}")
    
    return []

def generate_update_stock_alibaba_json():
    # 1. Charger l'ancien fichier JSON existant pour préserver les stocks si besoin
    produits_existants = {}
    if os.path.exists("update_stock_alibaba.json"):
        try:
            with open("update_stock_alibaba.json", "r", encoding="utf-8") as f:
                old_data = json.load(f)
                if isinstance(old_data, list):
                    for p in old_data:
                        pid = p.get("pid")
                        if pid:
                            produits_existants[pid] = p
        except Exception as e:
            print(f"⚠️ Impossible de lire l'ancien fichier JSON : {e}")

    tous_les_produits = produits_existants.copy()

    # 2. Recherche par mots-clés
    for keyword in MOTS_CLES_RECHERCHE:
        print(f"🔍 Recherche Alibaba en cours pour : '{keyword}'")
        items = recuperer_produits_alibaba_api(keyword)
        
        for item in items:
            pid = str(item.get("productId") or item.get("id"))
            if not pid:
                continue
                
            nom_original = item.get("subject") or item.get("title") or "Produit Alibaba"
            nom_fr = traduire_texte(nom_original)
            
            image_url = item.get("imageUrl") or item.get("image") or ""
            prix_base = float(item.get("price") or item.get("salePrice") or 0.0)
            
            # Construction des variantes
            variantes = []
            variants_list = item.get("skuList", [])
            
            if variants_list:
                for var in variants_list:
                    variantes.append({
                        "sku": str(var.get("skuId") or pid),
                        "vid": str(var.get("skuId") or "1"),
                        "taille": str(var.get("size") or "Standard"),
                        "couleur": str(var.get("color") or "Unique"),
                        "prix": float(var.get("price") or prix_base),
                        "poids": float(var.get("weight") or 0.5),
                        "stock": int(var.get("stock") or 100),
                        "shippingMethodFR": "Alibaba Standard Shipping",
                        "shippingCostFR": 0.0,
                        "shippingMethodUS": "Alibaba Standard Shipping",
                        "shippingCostUS": 0.0
                    })
            else:
                variantes.append({
                    "sku": pid,
                    "vid": pid,
                    "taille": "Standard",
                    "couleur": "Unique",
                    "prix": prix_base,
                    "poids": 0.5,
                    "stock": int(item.get("stock") or 100),
                    "shippingMethodFR": "Alibaba Standard Shipping",
                    "shippingCostFR": 0.0,
                    "shippingMethodUS": "Alibaba Standard Shipping",
                    "shippingCostUS": 0.0
                })

            tous_les_produits[pid] = {
                "dropshipping": "Alibaba",
                "pid": pid,
                "nom": nom_fr,
                "prixBase": round(prix_base, 2),
                "images": [image_url] if image_url else [],
                "variantes": variantes
            }

    resultat_final = list(tous_les_produits.values())

    # 3. Sauvegarde finale au format JSON pour le site
    with open("update_stock_alibaba.json", "w", encoding="utf-8") as f:
        json.dump(resultat_final, f, ensure_ascii=False, indent=4)
        
    print(f"🎉 Succès : {len(resultat_final)} produits enregistrés dans update_stock_alibaba.json")

if __name__ == "__main__":
    generate_update_stock_alibaba_json()
