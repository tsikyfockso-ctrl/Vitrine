// ==========================================
// CONFIGURATION DES MARGES & SURPLUS
// ==========================================
const MARGE_PRODUIT = 1.30;        // +30% de marge sur le prix de base du produit
const MARGE_EXPEDITION = 1.15;    // +15% de marge sur les frais de port

// Stockage global des taux de change actualisés (avec vos valeurs de référence par défaut)
let tauxDeChangeActuels = { "USD": 0.86, "EUR": 1.16 };

// --- 1. CONFIGURATION INITIALE ---
window.onload = async () => {
    await chargerTauxDeChange();
    
    // Chargement de chaque catégorie avec son fichier JSON attitré
    // La catégorie "femme" utilise update_stock.json
    chargerCategorie("update_stock.json", "product-container-femme");
    chargerCategorie("update_stock_acc_femme.json", "product-container-acc-femme");
    chargerCategorie("update_stock_homme.json", "product-container-homme");
    chargerCategorie("update_stock_acc_homme.json", "product-container-acc-homme");
    chargerCategorie("update_stock_enfant.json", "product-container-enfant");
    chargerCategorie("update_stock_acc_enfant.json", "product-container-acc-enfant");
    chargerCategorie("update_stock_sante.json", "product-container-sante");
    chargerCategorie("update_stock_maison.json", "product-container-maison");
    chargerCategorie("update_stock_electronique.json", "product-container-electrov");
    chargerCategorie("update_stock_informatique.json", "product-container-info");

    initialiserPays();
    initEventListeners();
};

// Récupération automatique des taux de change actualisés
async function chargerTauxDeChange() {
    try {
        const res = await fetch('https://open.er-api.com/v6/latest/USD');
        const data = await res.json();
        if (data && data.rates) {
            tauxDeChangeActuels = data.rates;
        }
    } catch (e) {
        console.warn("Impossible de charger les taux en direct, utilisation des valeurs de secours.", e);
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

    const taux = tauxDeChangeActuels[devise] || 1.0;
    return { devise, taux };
}

// --- 2. GESTION DU CHARGEMENT DES CATÉGORIES (JSON DISTINCTS) ---
async function chargerCategorie(jsonFileName, containerId) {
    const jsonUrl = jsonFileName + "?v=" + new Date().getTime(); // Anti-cache
    const container = document.getElementById(containerId);
    
    if (!container) {
        return;
    }

    container.innerHTML = `<p style="text-align:center; width:100%; padding:20px; font-size:0.85rem; color:#666;">Chargement...</p>`;

    try {
        const response = await fetch(jsonUrl);
        if (!response.ok) {
            throw new Error(`Erreur HTTP : ${response.status}`);
        }
        
        const stock = await response.json();
        
        if (Array.isArray(stock) && stock.length > 0) {
            localStorage.setItem("cached_" + containerId, JSON.stringify(stock));
            renderCategoryProducts(stock, container);
        } else {
            container.innerHTML = `<p style="text-align:center; width:100%; color:#888; font-size:0.85rem;">Aucun produit.</p>`;
        }
    } catch (error) {
        console.error("Erreur de chargement pour " + jsonFileName, error);
        
        const cachedStock = localStorage.getItem("cached_" + containerId);
        if (cachedStock) {
            renderCategoryProducts(JSON.parse(cachedStock), container);
        } else {
            container.innerHTML = `<p style="text-align:center; width:100%; color:#e74c3c; font-size:0.85rem;">Indisponible.</p>`;
        }
    }
}

// --- 3. AFFICHAGE DES PRODUITS PAR CONTENEUR ---
function renderCategoryProducts(stock, container) {
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

        let prixAffiche = ((prixBrut + MARGE_PRODUIT) * taux).toFixed(2);
        let nomProduit = p.nom || 'Sans nom';

        return `
            <div class="card" data-nom="${nomProduit.toLowerCase()}" onclick="openProductModalFromCache('${container.id}', ${index})">
                <div class="card-img-container">
                    <img src="${imgSrc || 'https://via.placeholder.com/300x200'}" alt="${nomProduit}" loading="lazy">
                </div>
                <h3>${nomProduit}</h3>
                <p>Prix : ${prixAffiche} ${devise}</p>
                <button onclick="event.stopPropagation(); openProductModalFromCache('${container.id}', ${index})">Voir les options</button>
            </div>
        `;
    }).join('');
}

// --- FONCTIONS DE DÉFILEMENT ---
function defilerProduits(direction, containerId = 'product-container-femme') {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const scrollAmount = 270; 
    
    if (direction === 'gauche') {
        container.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
    } else {
        container.scrollBy({ left: scrollAmount, behavior: 'smooth' });
    }
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

function openProductModalFromCache(containerId, index) {
    const cachedStock = localStorage.getItem("cached_" + containerId);
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
                let prixVarFinal = ((prixVarBrut + MARGE_PRODUIT) * taux).toFixed(2);

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

// --- 6. CALCUL DU PRIX, DU SKU ET DES FRAIS DE PORT ---
function calculateShipping() {
    if (!currentSelectedProduct || !currentSelectedProduct.variantes) return;

    const selectCountry = document.getElementById('modalCountrySelect');
    const countryCode = selectCountry ? selectCountry.value : "FR";
    
    const { devise, taux } = obtenirDeviseEtTaux(countryCode);

    const variantSelect = document.getElementById('modalVariantSelect');
    const selectedIndex = variantSelect ? parseInt(variantSelect.value) || 0 : 0;
    
    const varianteActuelle = currentSelectedProduct.variantes[selectedIndex] || currentSelectedProduct.variantes[0];

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

    let shippingCostFinal = (shippingCostBrut + MARGE_EXPEDITION) * taux;

    const modalShippingName = document.getElementById('modalShippingName');
    if (modalShippingName) {
        modalShippingName.innerText = shippingMethodName;
    }

    const modalShippingCost = document.getElementById('modalShippingCost');
    if (modalShippingCost) {
        modalShippingCost.innerText = `${shippingCostFinal.toFixed(2)} ${devise}`;
    }

    let currentPriceBrut = parseFloat(varianteActuelle.prix) || 0;
    let currentPriceFinal = (currentPriceBrut + MARGE_PRODUIT) * taux;

    const modalPriceElem = document.getElementById('modalPrice');
    if (modalPriceElem) {
        modalPriceElem.innerText = `${currentPriceFinal.toFixed(2)} ${devise}`;
    }

    let totalGlobal = currentPriceFinal + shippingCostFinal;
    const modalTotalCost = document.getElementById('modalTotalCost');
    if (modalTotalCost) {
        modalTotalCost.innerText = `${totalGlobal.toFixed(2)} ${devise}`;
    }

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

// --- GESTION DU DÉFILEMENT TACTILE (SWIPE) POUR CHAQUE CONTENEUR ---
document.addEventListener('DOMContentLoaded', () => {
    const containerIds = [
        'product-container-femme', 'product-container-acc-femme', 
        'product-container-homme', 'product-container-acc-homme', 
        'product-container-enfant', 'product-container-acc-enfant', 
        'product-container-sante', 'product-container-maison', 
        'product-container-electrov', 'product-container-info'
    ];

    containerIds.forEach(id => {
        const container = document.getElementById(id);
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

        container.addEventListener('mouseleave', () => { isDown = false; });
        container.addEventListener('mouseup', () => { isDown = false; });
        container.addEventListener('touchend', () => { isDown = false; });

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
});

// --- GESTION DU CHAT FLOTTANT ---
function toggleChat() {
    const chatPopup = document.getElementById('chat-popup');
    if (chatPopup) {
        chatPopup.classList.toggle('chat-hidden');
    }
}

const BIN_ID = (typeof window !== 'undefined' && window.CONFIG_BIN_ID) ? window.CONFIG_BIN_ID : "6a86df44f5f4af5e292ca904";
const API_KEY = (typeof window !== 'undefined' && window.CONFIG_API_KEY) ? window.CONFIG_API_KEY : "$2a$10$oWpiZV8hm0i.OzlsyPjBSOjhcp7i/oia15o2pK4d7ZWNXSdE3Piva";
const URL_API = `https://api.jsonbin.io/v3/b/${BIN_ID}`;

async function sendComment() {
    const nameInput = document.getElementById('userName');
    const msgInput = document.getElementById('userMsg');
    
    if (!nameInput || !msgInput) return;

    const name = nameInput.value.trim();
    const message = msgInput.value.trim();
    
    if (!name || !message) {
        alert("Veuillez remplir votre nom et votre message.");
        return;
    }
    
    try {
        const getRes = await fetch(URL_API + "/latest", {
            headers: { 'X-Master-Key': API_KEY }
        });
        const data = await getRes.json();
        
        let messages = (data.record && data.record.messages) ? data.record.messages : [];
        
        messages.push({
            nom: name,
            message: message,
            lu: false,
            reponse: ""
        });
        
        await fetch(URL_API, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-Master-Key': API_KEY
            },
            body: JSON.stringify({ messages: messages })
        });
        
        msgInput.value = '';
        nameInput.value = '';
        
        afficherMessagesClient();
        alert("Message envoyé avec succès !");
    } catch (e) {
        console.error("Erreur lors de l'envoi :", e);
    }
}

async function afficherMessagesClient() {
    if (!window.CONFIG_BIN_ID || window.CONFIG_BIN_ID.includes("...")) {
        return;
    }

    const currentUrlApi = `https://api.jsonbin.io/v3/b/${window.CONFIG_BIN_ID}`;
    const container = document.getElementById('client-messages');
    if (!container) return;
    
    try {
        const response = await fetch(currentUrlApi + "/latest", {
            headers: { 'X-Master-Key': window.CONFIG_API_KEY }
        });
        const data = await response.json();
        let messages = (data.record && data.record.messages) ? data.record.messages : [];
        
        if (messages.length === 0) {
            container.innerHTML = `<p style="font-size: 0.9rem; color: #777;">Aucun message pour le moment.</p>`;
            return;
        }
        
        let conversationsParClient = {};
        messages.forEach(m => {
            let nomClient = m.nom ? m.nom.trim() : "Anonyme";
            if (!conversationsParClient[nomClient]) {
                conversationsParClient[nomClient] = [];
            }
            conversationsParClient[nomClient].push(m);
        });
        
        let html = '';
        for (let nomClient in conversationsParClient) {
            html += `
                <div style="background: #fdfdfd; border: 1px solid #e0e0e0; border-radius: 6px; padding: 10px; margin-bottom: 12px;">
                    <div style="font-weight: bold; color: #2c3e50; font-size: 0.95rem; border-bottom: 2px solid #3498db; padding-bottom: 4px; margin-bottom: 8px;">
                        👤 Client : ${nomClient}
                    </div>
            `;
            
            conversationsParClient[nomClient].forEach(m => {
                const aRepondu = m.reponse && m.reponse.trim() !== "";
                
                html += `
                    <div style="background: #eef2f7; border-left: 3px solid #3498db; padding: 8px; margin-bottom: 8px; border-radius: 4px; font-size: 0.90rem;">
                        <p style="margin: 0; color: #333; word-break: break-word;">${m.message}</p>
                `;
                
                if (!aRepondu) {
                    html += `
                        <div style="margin-top: 6px; font-size: 0.75rem; color: #e67e22; font-style: italic;">
                            ⏳ En attente de réponse...
                        </div>
                    `;
                }
                
                html += `</div>`;
                
                if (aRepondu) {
                    html += `
                        <div style="background: #e8f8f5; border-left: 3px solid #2ecc71; padding: 8px; margin-bottom: 8px; margin-left: 10px; border-radius: 4px; font-size: 0.90rem;">
                            <strong style="color: #27ae60; font-size: 0.85rem;">🛍️ Mayah Store</strong>
                            <p style="margin: 4px 0 0 0; color: #333; word-break: break-word;">${m.reponse}</p>
                        </div>
                    `;
                }
            });
            
            html += `</div>`;
        }
        
        container.innerHTML = html;
    } catch (e) {
        console.error("Erreur de chargement des messages :", e);
    }
}

setInterval(afficherMessagesClient, 4000);
document.addEventListener('DOMContentLoaded', afficherMessagesClient);
