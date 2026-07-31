window.onload = () => {
    loadProductsFromCJ();
    initialiserPays();
    initEventListeners();
};

async function loadProductsFromCJ() {
    const jsonUrl = "update_stock.json?v=" + new Date().getTime();
    const container = document.getElementById('product-container');
    if (!container) return;

    container.innerHTML = `<p style="text-align:center; width:100%; padding:20px;">Chargement des produits...</p>`;

    try {
        const response = await fetch(jsonUrl);
        const stock = await response.json();
        if (Array.isArray(stock) && stock.length > 0) {
            localStorage.setItem("cached_cj_stock", JSON.stringify(stock));
            renderProducts(stock, container);
        } else {
            container.innerHTML = `<p style="text-align:center; width:100%; color:orange;">Aucun produit trouvé.</p>`;
        }
    } catch (error) {
        const cachedStock = localStorage.getItem("cached_cj_stock");
        if (cachedStock) {
            renderProducts(JSON.parse(cachedStock), container);
        }
    }
}

function renderProducts(stock, container) {
    container.innerHTML = stock.map((p, index) => {
        let rawImg = Array.isArray(p.images) ? p.images.find(img => img && img.trim() !== "") : p.images;
        let imgSrc = rawImg ? rawImg.trim() : "";
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

const listeDesPaysAvecFrais = [
    { code: "FR", nom: "France" }, { code: "DE", nom: "Allemagne" }, { code: "BE", nom: "Belgique" },
    { code: "CH", nom: "Suisse" }, { code: "CA", nom: "Canada" }, { code: "US", nom: "États-Unis" },
    { code: "GB", nom: "Royaume-Uni" }, { code: "ES", nom: "Espagne" }, { code: "IT", nom: "Italie" },
    { code: "CN", nom: "Chine" }, { code: "SN", nom: "Sénégal" }, { code: "CI", nom: "Côte d'Ivoire" },
    { code: "MA", nom: "Maroc" }, { code: "TN", nom: "Tunisie" }, { code: "DZ", nom: "Algérie" }
];

function initialiserPays() {
    const selectCountry = document.getElementById('modalCountrySelect');
    if (!selectCountry) return;
    selectCountry.innerHTML = listeDesPaysAvecFrais.map(pays => `
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
    document.getElementById('modalImg').src = rawImg ? `https://wsrv.nl/?url=${encodeURIComponent(rawImg)}&w=600&fit=cover` : '';
    document.getElementById('modalDesc').innerText = currentSelectedProduct.details || "Aucune description.";

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

// --- CALCUL TEMPS RÉEL VIA L'API CJ DROPSHIPPING ---
async function calculateShipping() {
    if (!currentSelectedProduct) return;
    
    const selectCountry = document.getElementById('modalCountrySelect');
    const countryCode = selectCountry ? selectCountry.value : "FR";
    
    const variantSelect = document.getElementById('modalVariantSelect');
    const selectedIndex = variantSelect ? variantSelect.value : 0;

    // Récupération du bon Variant ID (vid) de ce produit précis
    let vidsTab = Array.isArray(currentSelectedProduct.vids) ? currentSelectedProduct.vids : [];
    let currentVid = vidsTab[selectedIndex] || vidsTab[0] || "";

    const modalShippingCost = document.getElementById('modalShippingCost');
    modalShippingCost.innerText = "Calcul...";

    let shippingCostFinal = 5.00; // Valeur de secours par défaut

    if (currentVid) {
        try {
            // Appel vers l'API de calcul de fret de CJ
            const response = await fetch(`https://developers.cjdropshipping.com/api2.0/v1/logistic/freightCalculate`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                    // Note : Si vous exécutez ceci côté Front, assurez-vous de passer par un petit backend 
                    // pour cacher votre clé d'accès CJ, ou effectuez l'appel via votre serveur.
                },
                body: JSON.stringify({
                    startCountryCode: "CN",
                    endCountryCode: countryCode,
                    products: [{ quantity: 1, vid: currentVid }]
                })
            });
            const result = await response.json();
            if (result.success && result.data && result.data.length > 0) {
                shippingCostFinal = parseFloat(result.data[0].logisticPrice || 5.00);
            }
        } catch (e) {
            console.error("Erreur lors de la récupération des frais CJ en temps réel :", e);
        }
    }

    modalShippingCost.innerText = shippingCostFinal.toFixed(2);

    let prixTab = Array.isArray(currentSelectedProduct.prix) ? currentSelectedProduct.prix : [currentSelectedProduct.prix];
    let currentPrice = parseFloat(prixTab[selectedIndex] || prixTab[0] || 0);
    let totalGlobal = currentPrice + shippingCostFinal;

    document.getElementById('modalTotalCost').innerText = totalGlobal.toFixed(2) + " €";
}

function checkoutWithCard() {
    alert("Redirection vers le système de paiement sécurisé...");
}

function initEventListeners() {}
