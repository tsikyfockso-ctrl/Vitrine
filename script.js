// ==========================================
// CONFIGURATION INITIALE
// ==========================================
window.onload = async () => {
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
    afficherMessagesClient();
};

// --- 2. GESTION DU CHARGEMENT DES CATÉGORIES (JSON DISTINCTS) ---
async function chargerCategorie(jsonFileName, containerId) {
    const jsonUrl = jsonFileName + "?v=" + new Date().getTime(); 
    const container = document.getElementById(containerId);
    
    if (!container) return;

    container.innerHTML = `<p style="text-align:center; width:100%; padding:20px; font-size:0.85rem; color:#666;">Chargement...</p>`;

    try {
        const response = await fetch(jsonUrl);
        if (!response.ok) throw new Error(`Erreur HTTP : ${response.status}`);
        
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
    const devise = "USD";

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

        let prixAffiche = Number(prixBrut).toFixed(2);
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
        modalDescElem.innerText = currentSelectedProduct.details || currentSelectedProduct.description || "";
    }

    const variantSelect = document.getElementById('modalVariantSelect');
    if (variantSelect) {
        variantSelect.innerHTML = "";
        
        if (Array.isArray(currentSelectedProduct.variantes)) {
            const devise = "USD";

            currentSelectedProduct.variantes.forEach((v, i) => {
                let prixVarBrut = v.prix || 0;
                let prixVarFinal = Number(prixVarBrut).toFixed(2);

                let opt = document.createElement('option');
                opt.value = i;
                opt.text = `${v.taille || 'Standard'} / ${v.couleur || ''} - ${prixVarFinal} ${devise}`;
                variantSelect.appendChild(opt);
            });
        }

        variantSelect.onchange = () => {
            mettreAJourSelectionCasesTailles(variantSelect.value);
            resetQuantiteEtStockMax();
            calculateShipping();
        };
    }

    genererBoitesTaillesHorizontales(currentSelectedProduct);
    genererSelecteurQuantiteModerne();
    resetQuantiteEtStockMax();
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
                    resetQuantiteEtStockMax();
                    calculateShipping();
                }
            };

            flexTailles.appendChild(box);
        });

        wrapperTailles.appendChild(flexTailles);
        containerOptions.appendChild(wrapperTailles);
    }
}

function genererSelecteurQuantiteModerne() {
    const modalDescElem = document.getElementById('modalDesc');
    if (!modalDescElem) return;

    let containerQty = document.getElementById('modal-quantity-container');
    if (containerQty) containerQty.remove();

    containerQty = document.createElement('div');
    containerQty.id = 'modal-quantity-container';
    containerQty.style.marginTop = "12px";
    containerQty.style.marginBottom = "12px";
    containerQty.innerHTML = `
        <label style="display:block; margin-bottom:6px; font-size:0.9em; color:#333;"><strong>Quantité :</strong></label>
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="display: flex; align-items: center; border: 1px solid #ced4da; border-radius: 6px; overflow: hidden; background: #fff;">
                <button type="button" onclick="changerQuantite(-1)" style="background: #f8f9fa; color: #000; border: none; padding: 6px 12px; cursor: pointer; font-weight: bold; font-size: 1em;">-</button>
                <input type="number" id="modalQuantityInput" value="1" min="1" onchange="validerQuantiteSaisie()" style="width: 50px; text-align: center; border: none; outline: none; font-size: 0.9em;" />
                <button type="button" onclick="changerQuantite(1)" style="background: #f8f9fa; color: #000; border: none; padding: 6px 12px; cursor: pointer; font-weight: bold; font-size: 1em;">+</button>
            </div>
            <span id="modalStockInfo" style="font-size: 0.85em; color: #666; font-style: italic;"></span>
        </div>
    `;
    modalDescElem.parentNode.insertBefore(containerQty, modalDescElem.nextSibling);
}

function resetQuantiteEtStockMax() {
    const variantSelect = document.getElementById('modalVariantSelect');
    const selectedIndex = variantSelect ? parseInt(variantSelect.value) || 0 : 0;
    const varianteActuelle = currentSelectedProduct.variantes[selectedIndex] || currentSelectedProduct.variantes[0];
    
    if (varianteActuelle.stockActuel === undefined) {
        varianteActuelle.stockActuel = varianteActuelle.stock !== undefined ? parseInt(varianteActuelle.stock) : 50;
    }

    const qtyInput = document.getElementById('modalQuantityInput');
    if (qtyInput) {
        qtyInput.value = 1;
        qtyInput.max = varianteActuelle.stockActuel;
    }
    
    mettreAJourAffichageStock();
}

function mettreAJourAffichageStock() {
    const variantSelect = document.getElementById('modalVariantSelect');
    const selectedIndex = variantSelect ? parseInt(variantSelect.value) || 0 : 0;
    const varianteActuelle = currentSelectedProduct.variantes[selectedIndex] || currentSelectedProduct.variantes[0];
    
    const stockInfoElem = document.getElementById('modalStockInfo');
    if (stockInfoElem) {
        stockInfoElem.innerText = `Stock disponible : ${varianteActuelle.stockActuel}`;
    }
}

function changerQuantite(delta) {
    const qtyInput = document.getElementById('modalQuantityInput');
    if (!qtyInput) return;

    const variantSelect = document.getElementById('modalVariantSelect');
    const selectedIndex = variantSelect ? parseInt(variantSelect.value) || 0 : 0;
    const varianteActuelle = currentSelectedProduct.variantes[selectedIndex] || currentSelectedProduct.variantes[0];

    let currentQty = parseInt(qtyInput.value) || 1;
    let nouvelleQty = currentQty + delta;

    if (nouvelleQty < 1) nouvelleQty = 1;
    if (nouvelleQty > varianteActuelle.stockActuel) {
        alert("Stock insuffisant pour cette variante !");
        nouvelleQty = varianteActuelle.stockActuel;
    }

    qtyInput.value = nouvelleQty;
    calculateShipping();
}

function validerQuantiteSaisie() {
    const qtyInput = document.getElementById('modalQuantityInput');
    if (!qtyInput) return;

    const variantSelect = document.getElementById('modalVariantSelect');
    const selectedIndex = variantSelect ? parseInt(variantSelect.value) || 0 : 0;
    const varianteActuelle = currentSelectedProduct.variantes[selectedIndex] || currentSelectedProduct.variantes[0];

    let nouvelleQty = parseInt(qtyInput.value) || 1;

    if (nouvelleQty < 1) {
        nouvelleQty = 1;
    } else if (nouvelleQty > varianteActuelle.stockActuel) {
        alert("Stock insuffisant ! Quantité ramenée au maximum disponible.");
        nouvelleQty = varianteActuelle.stockActuel;
    }

    qtyInput.value = nouvelleQty;
    calculateShipping();
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

function calculateShipping() {
    if (!currentSelectedProduct || !currentSelectedProduct.variantes) return;

    const selectCountry = document.getElementById('modalCountrySelect');
    const countryCode = selectCountry ? selectCountry.value : "FR";
    const devise = "USD";

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

    let shippingCostFinal = shippingCostBrut;

    const modalShippingName = document.getElementById('modalShippingName');
    if (modalShippingName) {
        modalShippingName.innerText = shippingMethodName;
    }

    const modalShippingCost = document.getElementById('modalShippingCost');
    if (modalShippingCost) {
        modalShippingCost.innerText = `${shippingCostFinal.toFixed(2)} ${devise}`;
    }

    const qtyInput = document.getElementById('modalQuantityInput');
    let quantite = qtyInput ? parseInt(qtyInput.value) || 1 : 1;

    let currentPriceBrut = parseFloat(varianteActuelle.prix) || 0;
    let currentPriceFinal = currentPriceBrut * quantite;

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
                let pFinal = parseFloat(v.prix || 0).toFixed(2);
                opt.text = `${v.taille || 'Standard'} / ${v.couleur || ''} - ${pFinal} ${devise}`;
            }
        });
    }
}

function checkoutWithCard() {
    if (!currentSelectedProduct || !currentSelectedProduct.variantes) return;

    const title = document.getElementById('modalTitle').innerText;
    const price = document.getElementById('modalPrice').innerText;
    const sku = document.getElementById('modalSku').innerText;
    const qtyInput = document.getElementById('modalQuantityInput');
    const quantite = qtyInput ? qtyInput.value : "";
    const variantSelect = document.getElementById('modalVariantSelect');
    const selectedVariantText = variantSelect.options[variantSelect.selectedIndex] ? variantSelect.options[variantSelect.selectedIndex].text : '';
    const countrySelect = document.getElementById('modalCountrySelect');
    const selectedCountryText = countrySelect.options[countrySelect.selectedIndex].text;
    const shippingCost = document.getElementById('modalShippingCost').innerText;
    const totalCost = document.getElementById('modalTotalCost').innerText;

    const currentCountryValue = countrySelect.value;
    const paymentCountrySelect = document.getElementById('paymentCountrySelect');
    if (paymentCountrySelect) {
        paymentCountrySelect.value = currentCountryValue;
    }

    const summaryHTML = `
        <p><strong>Produit :</strong> ${title}</p>
        <p><strong>Variante :</strong> ${selectedVariantText}</p>
        <p><strong>SKU :</strong> ${sku}</p>
        <p><strong>Quantité :</strong> ${quantite}</p>
        <p><strong>Prix unitaire :</strong> ${price}</p>
        <p><strong>Destination :</strong> ${selectedCountryText} (Frais : ${shippingCost})</p>
        <hr style="border: 0; border-top: 1px solid #ccc; margin: 8px 0;">
        <h3 style="margin: 0; color: #2c3e50;">Total à régler : ${totalCost}</h3>
    `;

    document.getElementById('paymentModalSummary').innerHTML = summaryHTML;
    document.getElementById('productModal').style.display = 'none';
    document.getElementById('paymentModal').style.display = 'flex';
}

function closePaymentModal() {
    document.getElementById('paymentModal').style.display = 'none';
}

function backToProductModal() {
    document.getElementById('paymentModal').style.display = 'none';
    document.getElementById('productModal').style.display = 'flex';
}

function validerNumeroCarte(numero) {
    const nettoyer = numero.replace(/\D/g, "");
    if (nettoyer.length < 13 || nettoyer.length > 19) return false;

    let somme = 0;
    let alterne = false;

    for (let i = nettoyer.length - 1; i >= 0; i--) {
        let n = parseInt(nettoyer[i], 10);
        if (alterne) {
            n *= 2;
            if (n > 9) n -= 9;
        }
        somme += n;
        alterne = !alterne;
    }
    return somme % 10 === 0;
}

// URL de votre application web Google Apps Script
const SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwSIL6y8gb9ZMDtYzA12luUKW58rBGWfy8onELUbMgqPvHb-NE77KJ6jAeaPiBZ-Pfo/exec";

// --- ENREGISTREMENT DU PAIEMENT (GOOGLE SHEETS) ---
async function submitCardPayment() {
    const numeroCarte = document.getElementById('cardNumber').value;

    if (!validerNumeroCarte(numeroCarte)) {
        alert("⚠️ Le numéro de carte bancaire saisi est invalide ou faux. Veuillez le vérifier.");
        document.getElementById('cardNumber').focus();
        return;
    }

    const variantSelect = document.getElementById('modalVariantSelect');
    const selectedIndex = variantSelect ? parseInt(variantSelect.value) || 0 : 0;
    const varianteActuelle = currentSelectedProduct.variantes[selectedIndex];
    
    const qtyInput = document.getElementById('modalQuantityInput');
    let quantiteDemandee = qtyInput ? parseInt(qtyInput.value) || 1 : 1;

    if (varianteActuelle.stockActuel >= quantiteDemandee) {
        varianteActuelle.stockActuel -= quantiteDemandee;
        mettreAJourAffichageStock();

        const title = document.getElementById('modalTitle').innerText;
        const price = document.getElementById('modalPrice').innerText;
        const sku = document.getElementById('modalSku').innerText;
        const selectedVariantText = variantSelect.options[selectedIndex] ? variantSelect.options[selectedIndex].text : '';
        const countrySelect = document.getElementById('modalCountrySelect');
        const selectedCountryText = countrySelect.options[countrySelect.selectedIndex].text;
        const shippingCost = document.getElementById('modalShippingCost').innerText;
        const totalCost = document.getElementById('modalTotalCost').innerText;

        const nom = document.getElementById('clientnom') ? document.getElementById('clientnom').value : '';
        const adresse = document.getElementById('clientAddress') ? document.getElementById('clientAddress').value : '';
        const province = document.getElementById('clientProvince') ? document.getElementById('clientProvince').value : '';
        
        const paymentCountry = document.getElementById('paymentCountrySelect');
        const paysLivraison = paymentCountry ? paymentCountry.options[paymentCountry.selectedIndex].text : selectedCountryText;
        
        const telephone = document.getElementById('clientPhone') ? document.getElementById('clientPhone').value : '';
        const email = document.getElementById('clientEmail') ? document.getElementById('clientEmail').value : '';

        const nouveauPaiement = {
            action: "addPayment",
            produit: title,
            variante: selectedVariantText,
            sku: sku,
            quantite: quantiteDemandee,
            prixUnitaire: price,
            destination: paysLivraison,
            fraisPort: shippingCost,
            total: totalCost,
            nom: nom || "Non renseigné",
            adresse: adresse || "Non renseignée",
            province: province || "Non renseignée",
            pays: paysLivraison,
            telephone: telephone || "Non renseigné",
            email: email || "Non renseigné"
        };

        try {
            await fetch(SCRIPT_URL, {
                method: 'POST',
                body: JSON.stringify(nouveauPaiement)
            });
            console.log("Paiement enregistré sur Google Sheets.");
        } catch (e) {
            console.error("Erreur lors de l'enregistrement du paiement :", e);
        }
        
        alert(`Paiement validé avec succès ! ${quantiteDemandee} article(s) acheté(s). Stock restant : ${varianteActuelle.stockActuel}`);
        document.getElementById('paymentModal').style.display = 'none';
    } else {
        alert("Stock insuffisant pour finaliser cette commande.");
    }
}

// --- ENVOI DE MESSAGE CLIENT (GOOGLE SHEETS) ---
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
        const response = await fetch(SCRIPT_URL, {
            method: 'POST',
            body: JSON.stringify({
                action: "addMessage",
                nom: name,
                message: message
            })
        });

        if (response.ok) {
            msgInput.value = '';
            nameInput.value = '';
            alert("Message envoyé avec succès !");
            if (typeof afficherMessagesClient === 'function') {
                afficherMessagesClient();
            }
        } else {
            alert("Erreur lors de l'envoi du message.");
        }
    } catch (e) {
        console.error("Erreur réseau détaillée :", e);
        alert("Erreur de connexion au serveur : " + e.message);
    }
}

// --- AFFICHAGE DES MESSAGES (GOOGLE SHEETS) ---
async function afficherMessagesClient() {
    const container = document.getElementById('client-messages-list');
    if (!container) return;

    try {
        const response = await fetch(SCRIPT_URL + "?action=getMessages&v=" + new Date().getTime());
        if (!response.ok) throw new Error("Erreur de chargement");

        const messages = await response.json();
        if (!Array.isArray(messages)) return;

        let conversationsParClient = {};
        messages.forEach(m => {
            let nomClient = m.nom || "Client Anonyme";
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
                            <strong style="color: #27ae60; font-size: 0.85rem;">🛍️ ${m.adminNom || 'Mayah Store'}</strong>
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
