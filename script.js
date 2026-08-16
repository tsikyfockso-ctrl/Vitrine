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
                    <img src="${imgSrc || 'https://via.placeholder.com/300x200'}" alt="${p.nom || p.title || 'Produit'}" loading="lazy">
                </div>
                <h3>${p.nom || p.title || 'Sans nom'}</h3>
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
    
    selectCountry.onchange = () => calculateShipping();
}

let currentSelectedProduct = null;

function openProductModal(index) {
    const cachedStock = localStorage.getItem("cached_cj_stock");
    if (!cachedStock) return;
    const stock = JSON.parse(cachedStock);
    currentSelectedProduct = stock[index];
    if (!currentSelectedProduct) return;

    // Nom du produit
    document.getElementById('modalTitle').innerText = currentSelectedProduct.nom || currentSelectedProduct.title || 'Sans nom';
    
    // SKU
    const modalSkuElem = document.getElementById('modalSku'); 
    if (modalSkuElem) {
        modalSkuElem.innerText = currentSelectedProduct.sku || currentSelectedProduct.productSku || 'N/A';
    }

    // Image principale
    let rawImg = Array.isArray(currentSelectedProduct.images) ? currentSelectedProduct.images[0] : currentSelectedProduct.images;
    if (rawImg) {
        const modalImgElem = document.getElementById('modalImg');
        if (modalImgElem) {
            modalImgElem.src = `https://wsrv.nl/?url=${encodeURIComponent(rawImg)}&w=600&fit=cover`;
        }
    }
    
    // Description / Détails du produit
    const modalDescElem = document.getElementById('modalDesc');
    if (modalDescElem) {
        modalDescElem.innerText = currentSelectedProduct.details || currentSelectedProduct.description || currentSelectedProduct.desc || "Aucune description disponible.";
    }

    // Menu déroulant des variantes
    const variantSelect = document.getElementById('modalVariantSelect');
    if (variantSelect) {
        variantSelect.innerHTML = "";
        let prixTab = Array.isArray(currentSelectedProduct.prix) ? currentSelectedProduct.prix : [currentSelectedProduct.prix || currentSelectedProduct.price || 0];
        let taillesTab = Array.isArray(currentSelectedProduct.tailles) ? currentSelectedProduct.tailles : (Array.isArray(currentSelectedProduct.sizes) ? currentSelectedProduct.sizes : [currentSelectedProduct.tailles || currentSelectedProduct.size || 'Standard']);

        taillesTab.forEach((taille, i) => {
            let pVal = prixTab[i] !== undefined ? prixTab[i] : (prixTab[0] || "0");
            let opt = document.createElement('option');
            opt.value = i;
            opt.text = `${taille || 'Standard'} - ${pVal} €`;
            variantSelect.appendChild(opt);
        });

        variantSelect.onchange = () => {
            mettreAJourSelectionCasesTailles(variantSelect.value);
            calculateShipping();
        };
    }

    // Génération dynamique des boîtes de tailles horizontales sous la description
    genererBoitesTaillesHorizontales(currentSelectedProduct);

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

// --- 5. GÉNÉRATION DES CASES HORIZONTALES DE TAILLES / VARIANTES ---
function genererBoitesTaillesHorizontales(produit) {
    const modalDescElem = document.getElementById('modalDesc');
    if (!modalDescElem) return;

    // Supprimer l'ancien conteneur s'il existe pour éviter les doublons
    let containerOptions = document.getElementById('modal-horizontal-sizes');
    if (containerOptions) containerOptions.remove();

    // Création du conteneur des cases juste sous la description
    containerOptions = document.createElement('div');
    containerOptions.id = 'modal-horizontal-sizes';
    containerOptions.style.marginTop = "12px";
    containerOptions.style.marginBottom = "12px";
    modalDescElem.parentNode.insertBefore(containerOptions, modalDescElem.nextSibling);

    // Extraction dynamique des tailles/variantes du produit
    let taillesTab = [];
    
    if (Array.isArray(produit.tailles) && produit.tailles.length > 0) {
        taillesTab = produit.tailles;
    } else if (Array.isArray(produit.sizes) && produit.sizes.length > 0) {
        taillesTab = produit.sizes;
    } else if (Array.isArray(produit.variants) && produit.variants.length > 0) {
        taillesTab = produit.variants.map(v => v.taille || v.size || v.name || v.variantName || v.spec || "Option");
    } else if (Array.isArray(produit.options) && produit.options.length > 0) {
        taillesTab = produit.options;
    } else if (produit.taille) {
        taillesTab = [produit.taille];
    } else if (produit.size) {
        taillesTab = [produit.size];
    } else {
        const variantSelect = document.getElementById('modalVariantSelect');
        if (variantSelect && variantSelect.options.length > 0) {
            taillesTab = Array.from(variantSelect.options).map(opt => opt.text.split(' - ')[0]);
        }
    }

    if (taillesTab.length > 0 && taillesTab[0] !== null && taillesTab[0] !== undefined) {
        const wrapperTailles = document.createElement('div');
        wrapperTailles.innerHTML = `<label style="display:block; margin-bottom:6px; font-size:0.9em; color:#333;"><strong>Tailles / Variantes disponibles :</strong></label>`;
        
        const flexTailles = document.createElement('div');
        flexTailles.id = 'container-cases-tailles';
        flexTailles.style.display = "flex";
        flexTailles.style.gap = "8px";
        flexTailles.style.flexWrap = "wrap";

        taillesTab.forEach((taille, idx) => {
            const box = document.createElement('div');
            box.className = "modern-size-box";
            box.innerText = typeof taille === 'object' ? (taille.name || taille.taille || 'Option') : taille;
            box.style.padding = "6px 12px";
            box.style.border = "1px solid #ced4da";
            box.style.borderRadius = "6px";
            box.style.cursor = "pointer";
            box.style.fontSize = "0.85em";
            box.style.fontWeight = "500";
            box.style.transition = "all 0.2s ease";
            
            // Sélection par défaut de la première variante
            if (idx === 0) {
                box.style.background = "#007bff";
                box.style.color = "#fff";
                box.style.borderColor = "#007bff";
            } else {
                box.style.background = "#f8f9fa";
                box.style.color = "#333";
                box.style.borderColor = "#ced4da";
            }

            // Action au clic sur une case de taille/variante
            box.onclick = () => {
                const variantSelect = document.getElementById('modalVariantSelect');
                if (variantSelect && variantSelect.options[idx]) {
                    variantSelect.value = idx;
                    mettreAJourSelectionCasesTailles(idx);
                    calculateShipping();
                }
            };

            flexTailles.appendChild(box);
        });

        wrapperTailles.appendChild(flexTailles);
        containerOptions.appendChild(wrapperTailles);
    }
}

// Synchronisation visuelle des cases de tailles cliquées
function mettreAJourSelectionCasesTailles(selectedIndex) {
    const container = document.getElementById('container-cases-tailles');
    if (!container) return;

    Array.from(container.children).forEach((box, idx) => {
        if (idx === parseInt(selectedIndex)) {
            box.style.background = "#007bff";
            box.style.color = "#fff";
            box.style.borderColor = "#007bff";
        } else {
            box.style.background = "#f8f9fa";
            box.style.color = "#333";
            box.style.borderColor = "#ced4da";
        }
    });
}

// --- 6. AFFICHAGE DES FRAIS DE PORT ET DU PRIX TOTAL ---
function calculateShipping() {
    if (!currentSelectedProduct) return;

    const selectCountry = document.getElementById('modalCountrySelect');
    const countryCode = selectCountry ? selectCountry.value : "FR";

    let shippingCostFinal = 0;
    let shippingMethodName = "";

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

    const variantSelect = document.getElementById('modalVariantSelect');
    const selectedIndex = variantSelect ? parseInt(variantSelect.value) || 0 : 0;
    
    let prixTab = Array.isArray(currentSelectedProduct.prix) ? currentSelectedProduct.prix : [currentSelectedProduct.prix || currentSelectedProduct.price || 0];
    let rawPrice = prixTab[selectedIndex] !== undefined ? prixTab[selectedIndex] : (prixTab[0] || 0);
    let currentPrice = parseFloat(rawPrice) || 0;

    const modalPriceElem = document.getElementById('modalPrice');
    if (modalPriceElem) {
        modalPriceElem.innerText = currentPrice.toFixed(2) + " €";
    }

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
