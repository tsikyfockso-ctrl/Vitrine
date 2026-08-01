// --- 1. CONFIGURATION INITIALE ---
window.onload = () => {
    loadProductsFromCJ();
    initialiserPays();
    initEventListeners();
};

let allProducts = [];
let currentSelectedProduct = null;

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
            const stock = JSON.parse(cachedStock);
            renderProducts(stock, container);
        } else {
            container.innerHTML = `<p style="text-align:center; width:100%; color:red;">Erreur de chargement des produits. Vérifiez que update_stock.json est bien généré sur GitHub.</p>`;
        }
    }
}

// --- 3. AFFICHAGE DES PRODUITS SUR LA PAGE ---
function renderProducts(products, container) {
    allProducts = products;
    container.innerHTML = "";

    products.forEach((product, index) => {
        let prixTab = Array.isArray(product.prix) ? product.prix : [product.prix];
        let prixAffichage = prixTab[0] !== "" ? prixTab[0] : "0.00";

        let imagesTab = Array.isArray(product.images) ? product.images : [product.images];
        let rawImg = imagesTab[0] || "";
        let imageAffichage = rawImg ? `https://wsrv.nl/?url=${encodeURIComponent(rawImg)}&w=400&h=400&fit=cover` : "https://via.placeholder.com/300";

        let card = document.createElement('div');
        card.className = 'product-card';
        card.innerHTML = `
            <img src="${imageAffichage}" alt="${product.nom}">
            <h3>${product.nom}</h3>
            <p class="price">${prixAffichage} €</p>
            <button>Voir le produit</button>
        `;

        card.addEventListener('click', () => openProductModal(index));
        container.appendChild(card);
    });
}

// --- 4. GESTION DE LA MODALE PRODUIT ---
function openProductModal(productIndex) {
    const product = allProducts[productIndex];
    currentSelectedProduct = product;

    const modal = document.getElementById('productModal');
    if (!modal) return;
    
    modal.style.display = 'block';
    // Empêche le défilement de l'arrière-plan pendant que la modale est ouverte
    document.body.style.overflow = 'hidden'; 

    document.getElementById('modalTitle').innerText = product.nom;
    document.getElementById('modalDetails').innerText = product.details || "";
    document.getElementById('modalStock').innerText = "Stock disponible : " + (product.stock || 0);

    let imagesTab = Array.isArray(product.images) ? product.images : [product.images];
    let mainImgUrl = imagesTab[0] ? `https://wsrv.nl/?url=${encodeURIComponent(imagesTab[0])}&w=600&h=600&fit=cover` : "";
    const modalMainImage = document.getElementById('modalMainImage');
    if (modalMainImage) modalMainImage.src = mainImgUrl;

    let variantSelect = document.getElementById('modalVariantSelect');
    if (variantSelect) {
        variantSelect.innerHTML = "";
        let taillesTab = Array.isArray(product.tailles) ? product.tailles : [product.tailles];
        let prixTab = Array.isArray(product.prix) ? product.prix : [product.prix];

        taillesTab.forEach((taille, i) => {
            if (taille !== "" || prixTab[i] !== "") {
                let option = document.createElement('option');
                option.value = i;
                option.text = (taille ? taille : "Taille unique") + " - " + (prixTab[i] || "0.00") + " €";
                variantSelect.appendChild(option);
            }
        });
        variantSelect.onchange = calculateShipping;
    }

    // --- INTEGRATION DU BLOC DELAI DE LIVRAISON (AVEC INFOBULLE) ---
    let deliveryContainer = document.getElementById('modalDeliverySection');
    if (!deliveryContainer) {
        deliveryContainer = document.createElement('div');
        deliveryContainer.id = 'modalDeliverySection';
        const detailsElem = document.getElementById('modalDetails');
        if (detailsElem && detailsElem.parentNode) {
            detailsElem.parentNode.insertBefore(deliveryContainer, detailsElem.nextSibling);
        }
    }

    deliveryContainer.innerHTML = `
        <div style="margin-top: 15px; padding: 12px; background-color: #f9f9f9; border-radius: 8px; border: 1px solid #eaeaea;">
            <div style="display: flex; align-items: center; justify-content: space-between; position: relative;">
                <span style="font-weight: bold; font-size: 13px; color: #333; letter-spacing: 0.5px;">
                    🚚 DÉLAI DE LIVRAISON
                </span>
                
                <div class="tooltip-container" style="position: relative; display: inline-block; cursor: pointer;">
                    <span style="display: inline-flex; align-items: center; justify-content: center; width: 20px; height: 20px; background-color: #f97316; color: white; border-radius: 50%; font-size: 12px; font-weight: bold;">?</span>
                    
                    <span class="tooltip-text" style="visibility: hidden; width: 280px; background-color: #1f2937; color: #fff; text-align: left; border-radius: 6px; padding: 10px; position: absolute; z-index: 100; bottom: 125%; right: 0; opacity: 0; transition: opacity 0.3s; font-size: 11px; line-height: 1.4; box-shadow: 0px 4px 10px rgba(0,0,0,0.2);">
                        Ces chiffres représentent la probabilité que votre colis soit livré dans les délais indiqués, basés sur les données historiques de CJ pour le canal logistique sélectionné :<br><br>
                        • <strong>7-11 jours (51%)</strong> : Il y a environ 1 chance sur 2 que le colis arrive dans cette fourchette rapide.<br>
                        • <strong>12-14 jours (43%)</strong> : Une grande partie des colis arrivent également dans ce délai légèrement plus long.<br>
                        • <strong>15+ jours (6%)</strong> : Une petite minorité de colis prend plus de temps en raison d'imprévus (douane, météo, etc.).<br><br>
                        En résumé, la majorité des commandes (94%) devraient arriver sous 14 jours, mais il s'agit d'une estimation statistique et non d'une garantie absolue, car des facteurs externes comme le dédouanement peuvent influencer le délai final.
                    </span>
                </div>
            </div>

            <div style="margin-top: 8px; font-size: 13px; color: #4b5563;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>⚡ 7-11 jours</span>
                    <strong style="color: #16a34a;">51%</strong>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>📦 12-14 jours</span>
                    <strong style="color: #2563eb;">43%</strong>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span>⏳ 15+ jours</span>
                    <strong style="color: #dc2626;">6%</strong>
                </div>
            </div>
        </div>
    `;

    calculateShipping();
}

// --- 5. INITIALISATION DU SELECTEUR DE PAYS ---
function initialiserPays() {
    const selectCountry = document.getElementById('modalCountrySelect');
    if (!selectCountry) return;

    const paysDisponibles = [
        { code: "FR", nom: "France" },
        { code: "DE", nom: "Allemagne" },
        { code: "BE", nom: "Belgique" },
        { code: "ES", nom: "Espagne" },
        { code: "IT", nom: "Italie" },
        { code: "GB", nom: "Royaume-Uni" },
        { code: "CH", nom: "Suisse" },
        { code: "US", nom: "États-Unis" },
        { code: "CA", nom: "Canada" },
        { code: "SN", nom: "Sénégal" },
        { code: "CI", nom: "Côte d'Ivoire" },
        { code: "MA", nom: "Maroc" },
        { code: "TN", nom: "Tunisie" },
        { code: "DZ", nom: "Algérie" }
    ];

    selectCountry.innerHTML = "";
    paysDisponibles.forEach(p => {
        let opt = document.createElement('option');
        opt.value = p.code;
        opt.textContent = p.nom;
        if (p.code === "FR") opt.selected = true;
        selectCountry.appendChild(opt);
    });

    selectCountry.onchange = calculateShipping;
}

// --- 6. CALCUL DES FRAIS DE PORT ET DU PRIX TOTAL ---
function calculateShipping() {
    if (!currentSelectedProduct) return;

    const selectCountry = document.getElementById('modalCountrySelect');
    const countryCode = selectCountry ? selectCountry.value : "FR";

    let multiplicateurPays = 1.0;
    const zonesLoin = ["US", "CA", "CN"];
    const zonesTresLoin = ["SN", "CI", "MA", "TN", "DZ"];

    if (zonesTresLoin.includes(countryCode)) {
        multiplicateurPays = 2.0;
    } else if (zonesLoin.includes(countryCode)) {
        multiplicateurPays = 1.4;
    }

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

// --- 7. ECOUTEURS D'EVENEMENTS GLOBAUX ---
function initEventListeners() {
    const closeBtn = document.querySelector('.close-modal') || document.getElementById('closeModalBtn');
    const modal = document.getElementById('productModal');

    if (closeBtn && modal) {
        closeBtn.onclick = () => { 
            modal.style.display = 'none'; 
            document.body.style.overflow = 'auto'; // Rétablit le scroll de la page
        };
        window.onclick = (event) => {
            if (event.target === modal) { 
                modal.style.display = 'none'; 
                document.body.style.overflow = 'auto'; // Rétablit le scroll de la page
            }
        };
    }

    const checkoutBtn = document.getElementById('checkoutBtn');
    if (checkoutBtn) {
        checkoutBtn.onclick = checkoutWithCard;
    }
}

function checkoutWithCard() {
    alert("Redirection vers le système de paiement sécurisé...");
}
