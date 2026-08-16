// --- 1. CONFIGURATION INITIALE ---
window.onload = () => {
    loadProductsFromCJ();
    initialiserPays();
    initEventListeners();
};

// --- 2. GESTION DES PRODUITS (DEPUIS LE FICHIER JSON LOCAL) ---
async function loadProductsFromCJ() {
    const jsonUrl = "update_stock.json?v=" + new Date().getTime(); // Anti-cache
    const container = document.getElementById('product-container');
    
    if (!container) {
        console.error("Erreur : L'élément HTML avec l'id 'product-container' est introuvable !");
        return;
    }

    container.innerHTML = `<p style="text-align:center; width:100%; padding:20px;">Chargement des produits...</p>`;

    try {
        const response = await fetch(jsonUrl);
        if (!response.ok) {
            throw new Error(`Erreur HTTP : ${response.status}`);
        }
        
        const stock = await response.json();
        
        if (Array.isArray(stock) && stock.length > 0) {
            localStorage.setItem("cached_cj_stock", JSON.stringify(stock));
            renderProducts(stock, container);
        } else {
            container.innerHTML = `<p style="text-align:center; width:100%; color:orange;">Le fichier update_stock.json est vide.</p>`;
        }
    } catch (error) {
        console.error("Erreur de chargement :", error);
        
        const cachedStock = localStorage.getItem("cached_cj_stock");
        if (cachedStock) {
            renderProducts(JSON.parse(cachedStock), container);
        } else {
            container.innerHTML = `<p style="text-align:center; width:100%; color:red;">Impossible de charger les produits.</p>`;
        }
    }
}

// --- 3. AFFICHAGE DES PRODUITS AVEC PROXY D'IMAGES ---
function renderProducts(stock, container) {
    container.innerHTML = stock.map((p, index) => {
        let rawImg = Array.isArray(p.images) ? p.images.find(img => img && img.trim() !== "") : p.images;
        let imgSrc = rawImg ? rawImg.trim() : "";
        
        if (imgSrc.includes("alicdn.com") || imgSrc.includes("cj") || imgSrc.includes("aliexpress")) {
            imgSrc = `https://wsrv.nl/?url=${encodeURIComponent(imgSrc)}&w=400&fit=cover`;
        }

        let prixTab = Array.isArray(p.prix) ? p.prix : [p.prix];
        let prixAffiche = prixTab[0] !== undefined ? prixTab[0] : "0";
        
        return `
            <div class="card" onclick="openProductModal(${index})">
                <div class="card-img-container">
                    <img src="${imgSrc || 'https://via.placeholder.com/300x200'}" alt="${p.nom || 'Produit'}" loading="lazy">
                </div>
                <h3>${p.nom || 'Sans nom'}</h3>
                <p>Prix : ${prixAffiche} €</p>
                <button onclick="event.stopPropagation(); openProductModal(${index})">Voir les options</button>
            </div>
        `;
    }).join('');
}

// --- 4. LISTE DES PAYS ET GESTION DE LA MODALE ---
const listeDesPaysMondiaux = [
    { code: "FR", nom: "France" }, 
    { code: "US", nom: "États-Unis" }
];

function initialiserPays() {
    const selectCountry = document.getElementById('modalCountrySelect');
    if (!selectCountry) return;
    selectCountry.innerHTML = listeDesPaysMondiaux.map(pays => `
        <option value="${pays.code}">${pays.nom}</option>
    `).join('');
}

let currentSelectedProduct = null;

function openProductModal(index) {
    const cachedStock = localStorage.getItem("cached_cj_stock");
    if (!cachedStock) return;
    const stock = JSON.parse(cachedStock);
    currentSelectedProduct = stock[index];
    if (!currentSelectedProduct) return;

    document.getElementById('modalTitle').innerText = currentSelectedProduct.nom;
    
    // --- GESTION ET AFFICHAGE DU SKU ---
    const modalSkuElem = document.getElementById('modalSku');
    if (modalSkuElem) {
        modalSkuElem.innerText = currentSelectedProduct.sku || 'N/A';
    }

    let rawImg = Array.isArray(currentSelectedProduct.images) ? currentSelectedProduct.images[0] : currentSelectedProduct.images;
    if (rawImg) {
        document.getElementById('modalImg').src = `https://wsrv.nl/?url=${encodeURIComponent(rawImg)}&w=600&fit=cover`;
    }

    const variantSelect = document.getElementById('modalVariantSelect');
    if (variantSelect) {
        variantSelect.innerHTML = "";
        let prixTab = Array.isArray(currentSelectedProduct.prix) ? currentSelectedProduct.prix : [currentSelectedProduct.prix];
        let taillesTab = Array.isArray(currentSelectedProduct.tailles) ? currentSelectedProduct.tailles : [currentSelectedProduct.tailles];

        taillesTab.forEach((taille, i) => {
            let pVal = prixTab[i] !== undefined ? prixTab[i] : (prixTab[0] || "0");
            let opt = document.createElement('option');
            opt.value = i;
            opt.text = `${taille || 'Standard'} - ${pVal} €`;
            variantSelect.appendChild(opt);
        });
    }

    // Génération des couleurs cliquables si la propriété existe dans le JSON, sinon masque la section
    genererBoutonsCouleursDynamique(currentSelectedProduct);

    updateModalPriceAndSpecs();
    document.getElementById('productModal').style.display = 'flex';
}

function closeProductModal() {
    document.getElementById('productModal').style.display = 'none';
}

// --- 5. GESTION DES COULEURS CLIQUABLES ET TAILLES MODERNES ---
function genererBoutonsCouleursDynamique(produit) {
    // Crée ou récupère un conteneur de couleurs dans la modale s'il existe
    let containerCouleurs = document.getElementById('modal-color-options');
    if (!containerCouleurs) {
        // Si l'élément HTML n'existe pas encore dans votre modale, on peut l'insérer dynamiquement sous le select des variantes
        const variantSection = document.getElementById('modalVariantSelect')?.parentNode;
        if (variantSection) {
            containerCouleurs = document.createElement('div');
            containerCouleurs.id = 'modal-color-options';
            containerCouleurs.style.margin = "10px 0";
            variantSection.appendChild(containerCouleurs);
        }
    }

    if (!containerCouleurs) return;
    containerCouleurs.innerHTML = "";

    // Si le produit possède des couleurs dans son JSON
    if (produit.couleurs && Array.isArray(produit.couleurs) && produit.couleurs.length > 0) {
        containerCouleurs.style.display = "block";
        containerCouleurs.innerHTML = `<label style="display:block; margin-bottom:5px;"><strong>Couleurs disponibles :</strong></label>`;
        
        const flexDiv = document.createElement('div');
        flexDiv.style.display = "flex";
        flexDiv.style.gap = "8px";
        flexDiv.style.flexWrap = "wrap";

        produit.couleurs.forEach((couleur, idx) => {
            const btn = document.createElement('button');
            btn.type = "button";
            btn.innerText = couleur;
            btn.className = "color-option-btn";
            btn.style.padding = "6px 12px";
            btn.style.border = "1px solid #ccc";
            btn.style.borderRadius = "4px";
            btn.style.cursor = "pointer";
            btn.style.background = idx === 0 ? "#007bff" : "#fff";
            btn.style.color = idx === 0 ? "#fff" : "#000";

            btn.onclick = () => {
                // Style actif sur le bouton cliqué
                Array.from(flexDiv.children).forEach(b => {
                    b.style.background = "#fff";
                    b.style.color = "#000";
                });
                btn.style.background = "#007bff";
                btn.style.color = "#fff";

                // Vous pouvez lier le choix de la couleur ici si nécessaire
            };

            flexDiv.appendChild(btn);
        });
        containerCouleurs.appendChild(flexDiv);
    } else {
        containerCouleurs.style.display = "none";
    }
}

function updateModalPriceAndSpecs() {
    if (!currentSelectedProduct) return;

    const variantSelect = document.getElementById('modalVariantSelect');
    const selectedIndex = variantSelect ? parseInt(variantSelect.value) || 0 : 0;
    
    let taillesTab = Array.isArray(currentSelectedProduct.tailles) ? currentSelectedProduct.tailles : [currentSelectedProduct.tailles];
    let tailleActuelle = taillesTab[selectedIndex] || taillesTab[0] || "Standard";

    // --- STYLE MODERNE POUR LA TAILLE DANS LA DESCRIPTION ---
    const modalDescElem = document.getElementById('modalDesc');
    const descriptionOriginale = currentSelectedProduct.details || "Aucune description disponible.";
    
    if (modalDescElem) {
        modalDescElem.innerHTML = `
            <p>${descriptionOriginale}</p>
            <div style="margin-top: 12px; padding: 8px 12px; background: #f8f9fa; border-left: 4px solid #28a745; border-radius: 4px;">
                📏 <strong>Taille complète :</strong> <span class="complete-size" style="color: #2c3e50; font-weight: bold;">${tailleActuelle}</span>
            </div>
        `;
    }

    calculateShipping();
}

// --- 6. AFFICHAGE DES FRAIS DE PORT ET DU PRIX TOTAL ---
function calculateShipping() {
    if (!currentSelectedProduct) return;

    const selectCountry = document.getElementById('modalCountrySelect');
    const countryCode = selectCountry ? selectCountry.value : "FR";

    let shippingCostFinal = 0;
    let shippingMethodName = "";

    // Récupération dynamique des frais selon la France (FR) ou les États-Unis (US)[cite: 8]
    if (countryCode === "US") {
        shippingCostFinal = currentSelectedProduct.shippingUS !== undefined ? parseFloat(currentSelectedProduct.shippingUS) : 0;
        shippingMethodName = "USPS / Ligne Express (États-Unis)";
    } else {
        shippingCostFinal = currentSelectedProduct.shippingBase !== undefined ? parseFloat(currentSelectedProduct.shippingBase) : 0;
        shippingMethodName = "Colissimo / Ligne de Liquide (France)";
    }

    const modalShippingName = document.getElementById('modalShippingName');
    if (modalShippingName) {
        modalShippingName.innerText = shippingMethodName;
    }

    const modalShippingCost = document.getElementById('modalShippingCost');
    if (modalShippingCost) {
        modalShippingCost.innerText = shippingCostFinal.toFixed(2);
    }

    // Récupération du prix de la variante sélectionnée
    const variantSelect = document.getElementById('modalVariantSelect');
    const selectedIndex = variantSelect ? parseInt(variantSelect.value) || 0 : 0;
    
    let prixTab = Array.isArray(currentSelectedProduct.prix) ? currentSelectedProduct.prix : [currentSelectedProduct.prix];
    let rawPrice = prixTab[selectedIndex] !== undefined ? prixTab[selectedIndex] : (prixTab[0] || 0);
    let currentPrice = parseFloat(rawPrice) || 0;

    // Mise à jour du prix du produit dans la modale
    const modalPriceElem = document.getElementById('modalPrice');
    if (modalPriceElem) {
        modalPriceElem.innerText = currentPrice.toFixed(2) + " €";
    }

    // Calcul du total global (Prix du produit + Frais de port)
    let totalGlobal = currentPrice + shippingCostFinal;
    const modalTotalCost = document.getElementById('modalTotalCost');
    if (modalTotalCost) {
        modalTotalCost.innerText = totalGlobal.toFixed(2) + " €";
    }
}

function checkoutWithCard() {
    alert("Redirection vers le système de paiement sécurisé...");
}

function initEventListeners() {}

// --- FONCTION DE DÉFILEMENT DU CARROUSEL ---
function defilerProduits(direction) {
    const container = document.getElementById('product-container');
    if (!container) return;
    
    const scrollAmount = 270; 
    
    if (direction === 'gauche') {
        container.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
    } else {
        container.scrollBy({ left: scrollAmount, behavior: 'smooth' });
    }
}

// --- GESTION DU DÉFILEMENT TACTILE (SWIPE) ---
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('product-container');
    if (!container) return;

    let isDown = false;
    let startX;
    let scrollLeft;

    container.addEventListener('mousedown', (e) => {
        isDown = true;
        container.classList.add('active');
        startX = e.pageX - container.offsetLeft;
        scrollLeft = container.scrollLeft;
    });

    container.addEventListener('touchstart', (e) => {
        isDown = true;
        startX = e.touches[0].pageX - container.offsetLeft;
        scrollLeft = container.scrollLeft;
    }, { passive: true });

    container.addEventListener('mouseleave', () => {
        isDown = false;
    });

    container.addEventListener('mouseup', () => {
        isDown = false;
    });

    container.addEventListener('touchend', () => {
        isDown = false;
    });

    container.addEventListener('mousemove', (e) => {
        if (!isDown) return;
        e.preventDefault();
        const x = e.pageX - container.offsetLeft;
        const walk = (x - startX) * 2;
        container.scrollLeft = scrollLeft - walk;
    });

    container.addEventListener('touchmove', (e) => {
        if (!isDown) return;
        const x = e.touches[0].pageX - container.offsetLeft;
        const walk = (x - startX) * 2;
        container.scrollLeft = scrollLeft - walk;
    }, { passive: true });
});
