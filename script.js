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
    
    let rawImg = Array.isArray(currentSelectedProduct.images) ? currentSelectedProduct.images[0] : currentSelectedProduct.images;
    if (rawImg) {
        document.getElementById('modalImg').src = `https://wsrv.nl/?url=${encodeURIComponent(rawImg)}&w=600&fit=cover`;
    }
    
    document.getElementById('modalDesc').innerText = currentSelectedProduct.details || "Aucune description disponible.";

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

    updateModalPriceAndSpecs();
    document.getElementById('productModal').style.display = 'flex';
}

function closeProductModal() {
    document.getElementById('productModal').style.display = 'none';
}

function updateModalPriceAndSpecs() {
    if (!currentSelectedProduct) return;
    calculateShipping();
}

// --- 5. AFFICHAGE DES FRAIS DE PORT ET DU PRIX TOTAL ---
function calculateShipping() {
    if (!currentSelectedProduct) return;

    const selectCountry = document.getElementById('modalCountrySelect');
    const countryCode = selectCountry ? selectCountry.value : "FR";

    let shippingCostFinal = 0;
    let shippingMethodName = "";

    // Récupération des frais selon le pays (calculés par Python)
    if (countryCode === "US") {
        shippingCostFinal = currentSelectedProduct.shippingUS !== undefined ? parseFloat(currentSelectedProduct.shippingUS) : 0;
        shippingMethodName = "USPS / Ligne Express (États-Unis)";
    } else {
        shippingCostFinal = currentSelectedProduct.shippingBase !== undefined ? parseFloat(currentSelectedProduct.shippingBase) : 0;
        shippingMethodName = "Colissimo / Ligne de Liquide (France)";
    }

    // Affichage de la méthode de livraison
    const modalShippingName = document.getElementById('modalShippingName');
    if (modalShippingName) {
        modalShippingName.innerText = shippingMethodName;
    }

    // Affichage du coût de livraison estimé
    const modalShippingCost = document.getElementById('modalShippingCost');
    if (modalShippingCost) {
        modalShippingCost.innerText = shippingCostFinal.toFixed(2);
    }

    // 1. Récupération du prix du produit selon la variante sélectionnée
    const variantSelect = document.getElementById('modalVariantSelect');
    const selectedIndex = variantSelect ? parseInt(variantSelect.value) || 0 : 0;
    
    let prixTab = Array.isArray(currentSelectedProduct.prix) ? currentSelectedProduct.prix : [currentSelectedProduct.prix];
    let rawPrice = prixTab[selectedIndex] !== undefined ? prixTab[selectedIndex] : (prixTab[0] || 0);
    let currentPrice = parseFloat(rawPrice) || 0;

    // 2. MISE À JOUR AUTOMATIQUE DU PRIX DU PRODUIT DANS LA MODALE (#modalPrice)
    const modalPriceElem = document.getElementById('modalPrice');
    if (modalPriceElem) {
        modalPriceElem.innerText = currentPrice.toFixed(2) + " €";
    }

    // 3. Calcul et affichage du total global (Prix du produit + Frais de port)
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
