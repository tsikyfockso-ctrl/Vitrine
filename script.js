// ==========================================
// CONFIGURATION DES MARGES & SURPLUS
// ==========================================
const MARGE_PRODUIT = 1.30;       // +30% de marge sur le prix de base du produit
const MARGE_EXPEDITION = 1.15;    // +15% de marge sur les frais de port

// Stockage global des taux de change actualisés
let tauxDeChangeActuels = { "USD": 0.86, "EUR": 1.16 };

// --- 1. CONFIGURATION INITIALE ---
window.onload = async () => {
    await chargerTauxDeChange();
    loadProductsFromCJ();
    initialiserPays();
    initEventListeners();
};

// Récupération automatique des taux de change en direct
async function chargerTauxDeChange() {
    try {
        const res = await fetch('https://open.er-api.com/v6/latest/USD');
        const data = await res.json();
        if (data && data.rates) {
            tauxDeChangeActuels = data.rates;
        }
    } catch (e) {
        console.warn("Impossible de charger les taux en direct, utilisation des valeurs par défaut.", e);
    }
}

// Obtenir la devise et le taux selon le code pays (limité à US et FR)
function obtenirDeviseEtTaux(countryCode) {
    let devise = "USD";
    if (countryCode.toUpperCase() === "FR") {
        devise = "EUR";
    } else if (countryCode.toUpperCase() === "US") {
        devise = "USD";
    }

    const taux = tauxDeChangeActuels[devise] || 0.86;
    return { devise, taux };
}

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

// --- 3. AFFICHAGE DES PRODUITS ---
function renderProducts(stock, container) {
    // Par défaut affichage catalogue basé sur la France (EUR)
    const { devise, taux } = obtenirDeviseEtTaux("FR");

    container.innerHTML = stock.map((p, index) => {
        let rawImg = Array.isArray(p.images) ? p.images.find(img => img && img.trim() !== "") : p.images;
        let imgSrc = rawImg ? rawImg.trim() : "";
        
        if (imgSrc.includes("alicdn.com") || imgSrc.includes("cj") || imgSrc.includes("aliexpress")) {
            imgSrc = `https://wsrv.nl/?url=${encodeURIComponent(imgSrc)}&w=400&fit=cover`;
        }

        let prixBrut = p.prixBase || 0;
        if (p.variantes && p.variantes.length > 0 && p.variantes[0].prix !== undefined) {
            prixBrut = p.variantes[0].prix;
        }

        // Application de la marge + conversion devise
        let prixAffiche = (prixBrut * MARGE_PRODUIT * taux).toFixed(2);
        
        return `
            <div class="card" onclick="openProductModal(${index})">
                <div class="card-img-container">
                    <img src="${imgSrc || 'https://via.placeholder.com/300x200'}" alt="${p.nom || 'Produit'}" loading="lazy">
                </div>
                <h3>${p.nom || 'Sans nom'}</h3>
                <p>Prix : ${prixAffiche} ${devise}</p>
                <button onclick="event.stopPropagation(); openProductModal(${index})">Voir les options</button>
            </div>
        `;
    }).join('');
}

// --- 4. LISTE DES PAYS (RESTREINTE À US ET FR) ET GESTION DE LA MODALE ---
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

    document.getElementById('modalTitle').innerText = currentSelectedProduct.nom || 'Sans nom';

    let rawImg = Array.isArray(currentSelectedProduct.images) ? currentSelectedProduct.images[0] : currentSelectedProduct.images;
    if (rawImg) {
        const modalImgElem = document.getElementById('modalImg');
        if (modalImgElem) {
            modalImgElem.src = `https://wsrv.nl/?url=${encodeURIComponent(rawImg)}&w=600&fit=cover`;
        }
    }
    
    const modalDescElem = document.getElementById('modalDesc');
    if (modalDescElem) {
        modalDescElem.innerText = currentSelectedProduct.details || currentSelectedProduct.description || "Aucune description disponible.";
    }

    const variantSelect = document.getElementById('modalVariantSelect');
    if (variantSelect) {
        variantSelect.innerHTML = "";
        
        if (Array.isArray(currentSelectedProduct.variantes)) {
            const selectCountry = document.getElementById('modalCountrySelect');
            const countryCode = selectCountry ? selectCountry.value : "FR";
            const { devise, taux } = obtenirDeviseEtTaux(countryCode);

            currentSelectedProduct.variantes.forEach((v, i) => {
                let prixVarBrut = v.prix || 0;
                let prixVarFinal = (prixVarBrut * MARGE_PRODUIT * taux).toFixed(2);

                let opt = document.createElement('option');
                opt.value = i;
                opt.text = `${v.taille || 'Standard'} / ${v.couleur || ''} - ${prixVarFinal} ${devise}`;
                variantSelect.appendChild(opt);
            });
        }

        variantSelect.onchange = () => {
            mettreAJourSelectionCasesTailles(variantSelect.value);
            calculateShipping();
        };
    }

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

// --- 5. GÉNÉRATION DES CASES HORIZONTALES DE VARIANTES ---
function genererBoitesTaillesHorizontales(produit) {
    const modalDescElem = document.getElementById('modalDesc');
    if (!modalDescElem) return;

    let containerOptions = document.getElementById('modal-horizontal-sizes');
    if (containerOptions) containerOptions.remove();

    containerOptions = document.createElement('div');
    containerOptions.id = 'modal-horizontal-sizes';
    containerOptions.style.marginTop = "12px";
    containerOptions.style.marginBottom = "12px";
    modalDescElem.parentNode.insertBefore(containerOptions, modalDescElem.nextSibling);

    if (Array.isArray(produit.variantes) && produit.variantes.length > 0) {
        const wrapperTailles = document.createElement('div');
        wrapperTailles.innerHTML = `<label style="display:block; margin-bottom:6px; font-size:0.9em; color:#333;"><strong>Tailles / Variantes disponibles :</strong></label>`;
        
        const flexTailles = document.createElement('div');
        flexTailles.id = 'container-cases-tailles';
        flexTailles.style.display = "flex";
        flexTailles.style.gap = "8px";
        flexTailles.style.flexWrap = "wrap";

        produit.variantes.forEach((v, idx) => {
            const box = document.createElement('div');
            box.className = "modern-size-box";
            box.innerText = `${v.taille || 'Option'} (${v.couleur || ''})`;
            box.style.padding = "6px 12px";
            box.style.border = "1px solid #ced4da";
            box.style.borderRadius = "6px";
            box.style.cursor = "pointer";
            box.style.fontSize = "0.85em";
            box.style.fontWeight = "500";
            box.style.transition = "all 0.2s ease";
            
            if (idx === 0) {
                box.style.background = "#007bff";
                box.style.color = "#fff";
                box.style.borderColor = "#007bff";
            } else {
                box.style.background = "#f8f9fa";
                box.style.color = "#333";
                box.style.borderColor = "#ced4da";
            }

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

// --- 6. CALCUL DU PRIX, DU SKU ET DES FRAIS DE PORT (AVEC MARGES & DEVISES) ---
function calculateShipping() {
    if (!currentSelectedProduct || !currentSelectedProduct.variantes) return;

    const selectCountry = document.getElementById('modalCountrySelect');
    const countryCode = selectCountry ? selectCountry.value : "FR";
    
    // Récupération de la devise et du taux de change mis à jour (EUR pour FR, USD pour US)
    const { devise, taux } = obtenirDeviseEtTaux(countryCode);

    const variantSelect = document.getElementById('modalVariantSelect');
    const selectedIndex = variantSelect ? parseInt(variantSelect.value) || 0 : 0;
    
    const varianteActuelle = currentSelectedProduct.variantes[selectedIndex] || currentSelectedProduct.variantes[0];

    // Mise à jour du SKU spécifique à la variante sélectionnée
    const modalSkuElem = document.getElementById('modalSku');
    if (modalSkuElem) {
        modalSkuElem.innerText = varianteActuelle.sku || 'N/A';
    }

    let shippingCostBrut = 0;
    let shippingMethodName = "";

    if (countryCode === "US") {
        shippingCostBrut = varianteActuelle.shippingCostUS !== undefined ? parseFloat(varianteActuelle.shippingCostUS) : 0;
        shippingMethodName = varianteActuelle.shippingMethodUS || "YunExpress Ordinary";
    } else {
        shippingCostBrut = varianteActuelle.shippingCostFR !== undefined ? parseFloat(varianteActuelle.shippingCostFR) : 0;
        shippingMethodName = varianteActuelle.shippingMethodFR || "CJPacket Ordinary I";
    }

    // Application du surplus sur les frais de port + conversion devise
    let shippingCostFinal = shippingCostBrut * MARGE_EXPEDITION * taux;

    const modalShippingName = document.getElementById('modalShippingName');
    if (modalShippingName) {
        modalShippingName.innerText = shippingMethodName;
    }

    const modalShippingCost = document.getElementById('modalShippingCost');
    if (modalShippingCost) {
        modalShippingCost.innerText = `${shippingCostFinal.toFixed(2)} ${devise}`;
    }

    // Application du surplus sur le prix du produit + conversion devise
    let currentPriceBrut = parseFloat(varianteActuelle.prix) || 0;
    let currentPriceFinal = currentPriceBrut * MARGE_PRODUIT * taux;

    const modalPriceElem = document.getElementById('modalPrice');
    if (modalPriceElem) {
        modalPriceElem.innerText = `${currentPriceFinal.toFixed(2)} ${devise}`;
    }

    // Calcul du total global
    let totalGlobal = currentPriceFinal + shippingCostFinal;
    const modalTotalCost = document.getElementById('modalTotalCost');
    if (modalTotalCost) {
        modalTotalCost.innerText = `${totalGlobal.toFixed(2)} ${devise}`;
    }

    // Actualiser également le libellé du menu déroulant des variantes avec la nouvelle devise/marge
    if (variantSelect) {
        Array.from(variantSelect.options).forEach((opt, i) => {
            const v = currentSelectedProduct.variantes[i];
            if (v) {
                let pFinal = (parseFloat(v.prix || 0) * MARGE_PRODUIT * taux).toFixed(2);
                opt.text = `${v.taille || 'Standard'} / ${v.couleur || ''} - ${pFinal} ${devise}`;
            }
        });
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
