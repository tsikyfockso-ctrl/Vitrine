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
        
        // Proxy wsrv.nl pour forcer l'affichage des images en provenance de CJ/Aliexpress
        if (imgSrc.includes("alicdn.com") || imgSrc.includes("cj") || imgSrc.includes("aliexpress")) {
            imgSrc = `https://wsrv.nl/?url=${encodeURIComponent(imgSrc)}&w=400&fit=cover`;
        }

        let prixAffiche = Array.isArray(p.prix) ? (p.prix[0] || "0") : (p.prix || "0");
        
        return `
            <div class="card" onclick="openProductModal(${index})">
                <div class="card-img-container">
                    <img src="${imgSrc || 'https://via.placeholder.com/300x200'}" alt="${p.nom}" loading="lazy">
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
    { code: "FR", nom: "France" }, { code: "DE", nom: "Allemagne" }, { code: "BE", nom: "Belgique" },
    { code: "CH", nom: "Suisse" }, { code: "CA", nom: "Canada" }, { code: "US", nom: "États-Unis" },
    { code: "GB", nom: "Royaume-Uni" }, { code: "ES", nom: "Espagne" }, { code: "IT", nom: "Italie" },
    { code: "SN", nom: "Sénégal" }, { code: "CI", nom: "Côte d'Ivoire" }, { code: "MA", nom: "Maroc" },
    { code: "TN", nom: "Tunisie" }, { code: "DZ", nom: "Algérie" }, { code: "CN", nom: "Chine" }
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
            if (taille && taille.trim() !== "") {
                let pVal = prixTab[i] || prixTab[0] || "0";
                let opt = document.createElement('option');
                opt.value = i;
                opt.text = `${taille} - ${pVal} €`;
                variantSelect.appendChild(opt);
            }
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
    const variantSelect = document.getElementById('modalVariantSelect');
    const selectedIndex = variantSelect ? variantSelect.value : 0;

    let prixTab = Array.isArray(currentSelectedProduct.prix) ? currentSelectedProduct.prix : [currentSelectedProduct.prix];
    let currentPrice = parseFloat(prixTab[selectedIndex] || prixTab[0] || 0);

    document.getElementById('modalPrice').innerText = currentPrice.toFixed(2) + " €";
    calculateShipping();
}

// --- 5. CALCUL DYNAMIQUE DES FRAIS DE PORT PAR PAYS ---
function calculateShipping() {
    if (!currentSelectedProduct) return;

    const selectCountry = document.getElementById('modalCountrySelect');
    const countryCode = selectCountry ? selectCountry.value : "FR";

    let multiplicateurPays = 1.0;

    // Coefficients par zone géographique
    const zonesLoin = ["US", "CA", "CN"];
    const zonesTresLoin = ["SN", "CI", "MA", "TN", "DZ"];

    if (zonesTresLoin.includes(countryCode)) {
        multiplicateurPays = 2.0;
    } else if (zonesLoin.includes(countryCode)) {
        multiplicateurPays = 1.4;
    }

    // Récupération de la base calculée par Python selon le poids réel du produit
    let shippingBaseProduit = currentSelectedProduct && currentSelectedProduct.shippingBase !== undefined 
        ? parseFloat(currentSelectedProduct.shippingBase) 
        : 4.00;

    let shippingCostFinal = shippingBaseProduit * multiplicateurPays;

    const modalShippingCost = document.getElementById('modalShippingCost');
    if (modalShippingCost) modalShippingCost.innerText = shippingCostFinal.toFixed(2);

    const variantSelect = document.getElementById('modalVariantSelect');
    const selectedIndex = variantSelect ? variantSelect.value : 0;
    let prixTab = Array.isArray(currentSelectedProduct.prix) ? currentSelectedProduct.prix : [currentSelectedProduct.prix];
    let currentPrice = parseFloat(prixTab[selectedIndex] || prixTab[0] || 0);

    let totalGlobal = currentPrice + shippingCostFinal;
    const modalTotalCost = document.getElementById('modalTotalCost');
    if (modalTotalCost) modalTotalCost.innerText = totalGlobal.toFixed(2) + " €";
}

function checkoutWithCard() {
    alert("Redirection vers le système de paiement sécurisé...");
}

function initEventListeners() {}

// --- FONCTION DE DÉFILEMENT DU CARROUSEL ---
function defilerProduits(direction) {
    const container = document.getElementById('product-container');
    if (!container) return;
    
    // Défile de la largeur d'une carte environ (270px avec l'écart)
    const scrollAmount = 270; 
    
    if (direction === 'gauche') {
        container.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
    } else {
        container.scrollBy({ left: scrollAmount, behavior: 'smooth' });
    }
}
