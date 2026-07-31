// --- 1. CONFIGURATION INITIALE ---
window.onload = () => {
    loadProductsFromCJ();
    initialiserPays();
    initEventListeners();
};

// --- 2. GESTION DES PRODUITS (DEPUIS LE FICHIER JSON LOCAL) ---
async function loadProductsFromCJ() {
    const jsonUrl = "update_stock.json?v=" + new Date().getTime(); // Anti-cache radical
    const container = document.getElementById('product-container');
    
    if (!container) {
        console.error("Erreur : L'élément HTML avec l'id 'product-container' est introuvable !");
        return;
    }

    container.innerHTML = `<p style="text-align:center; width:100%; padding:20px;">Chargement des produits...</p>`;

    try {
        const response = await fetch(jsonUrl);
        if (!response.ok) {
            throw new Error(`Erreur HTTP : ${response.status} (Le fichier update_stock.json est introuvable)`);
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
        
        // Secours : si le fetch échoue, on essaie le cache local
        const cachedStock = localStorage.getItem("cached_cj_stock");
        if (cachedStock) {
            try {
                const stock = JSON.parse(cachedStock);
                renderProducts(stock, container);
                return;
            } catch (e) {}
        }
        
        container.innerHTML = `
            <div style="text-align:center; width:100%; padding:20px; color:red;">
                <p><strong>Impossible de charger le catalogue.</strong></p>
                <p>Vérifiez que le fichier <code>update_stock.json</code> est bien placé à la racine du projet.</p>
            </div>`;
    }
}

// --- 3. AFFICHAGE DES PRODUITS SUR LA VITRINE ---
function renderProducts(stock, container) {
    container.innerHTML = stock.map((p, index) => {
        let rawImg = "";
        if (Array.isArray(p.images) && p.images.length > 0) {
            rawImg = p.images.find(img => img && img.trim() !== "") || "";
        } else if (typeof p.images === "string") {
            rawImg = p.images;
        }

        let imgSrc = rawImg.trim() !== "" ? rawImg : "https://via.placeholder.com/300x200?text=Image+Indisponible";
        
        if (imgSrc.includes("alicdn.com") || imgSrc.includes("cj") || imgSrc.includes("aliexpress")) {
            imgSrc = `https://wsrv.nl/?url=${encodeURIComponent(imgSrc)}&w=400&fit=cover`;
        }

        let prixAffiche = "0";
        if (Array.isArray(p.prix) && p.prix.length > 0) {
            prixAffiche = p.prix[0] || "0";
        } else {
            prixAffiche = p.prix || "0";
        }
        
        return `
            <div class="card" onclick="openProductModal(${index})">
                <div class="card-img-container">
                    <img src="${imgSrc}" alt="${p.nom || 'Produit'}" loading="lazy">
                </div>
                <h3>${p.nom || 'Sans nom'}</h3>
                <p>Prix : ${prixAffiche} €</p>
                <button onclick="event.stopPropagation(); openProductModal(${index})">Voir les options</button>
            </div>
        `;
    }).join('');
}

// --- 4. LISTE MONDIALE DES PAYS AVEC FRAIS DE PORT ---
const listeDesPaysAvecFrais = [
    { code: "FR", nom: "France", shippingCost: 5.50 },
    { code: "DE", nom: "Allemagne", shippingCost: 5.00 },
    { code: "BE", nom: "Belgique", shippingCost: 5.00 },
    { code: "CH", nom: "Suisse", shippingCost: 7.00 },
    { code: "CA", nom: "Canada", shippingCost: 9.50 },
    { code: "US", nom: "États-Unis", shippingCost: 8.50 },
    { code: "GB", nom: "Royaume-Uni", shippingCost: 6.00 },
    { code: "ES", nom: "Espagne", shippingCost: 5.50 },
    { code: "IT", nom: "Italie", shippingCost: 5.50 },
    { code: "CN", nom: "Chine", shippingCost: 2.00 },
    { code: "AF", nom: "Afghanistan", shippingCost: 15.00 },
    { code: "AL", nom: "Albanie", shippingCost: 10.00 },
    { code: "DZ", nom: "Algérie", shippingCost: 12.00 },
    { code: "AD", nom: "Andorre", shippingCost: 8.00 },
    { code: "AO", nom: "Angola", shippingCost: 15.00 },
    { code: "AG", nom: "Antigua-et-Barbuda", shippingCost: 14.00 },
    { code: "SA", nom: "Arabie saoudite", shippingCost: 9.00 },
    { code: "AR", nom: "Argentine", shippingCost: 12.00 },
    { code: "AM", nom: "Arménie", shippingCost: 11.00 },
    { code: "AU", nom: "Australie", shippingCost: 8.50 },
    { code: "AT", nom: "Autriche", shippingCost: 5.50 },
    { code: "AZ", nom: "Azerbaïdjan", shippingCost: 11.00 },
    { code: "BS", nom: "Bahamas", shippingCost: 12.00 },
    { code: "BH", nom: "Bahreïn", shippingCost: 10.00 },
    { code: "BD", nom: "Bangladesh", shippingCost: 10.00 },
    { code: "BB", nom: "Barbade", shippingCost: 12.00 },
    { code: "BZ", nom: "Belize", shippingCost: 13.00 },
    { code: "BJ", nom: "Bénin", shippingCost: 15.00 },
    { code: "BT", nom: "Bhoutan", shippingCost: 12.00 },
    { code: "BY", nom: "Biélorussie", shippingCost: 10.00 },
    { code: "BO", nom: "Bolivie", shippingCost: 13.00 },
    { code: "BA", nom: "Bosnie-Herzégovine", shippingCost: 9.50 },
    { code: "BW", nom: "Botswana", shippingCost: 14.00 },
    { code: "BR", nom: "Brésil", shippingCost: 11.00 },
    { code: "BN", nom: "Brunéi", shippingCost: 9.00 },
    { code: "BG", nom: "Bulgarie", shippingCost: 6.50 },
    { code: "BF", nom: "Burkina Faso", shippingCost: 15.00 },
    { code: "BI", nom: "Burundi", shippingCost: 16.00 },
    { code: "KH", nom: "Cambodge", shippingCost: 8.50 },
    { code: "CM", nom: "Cameroun", shippingCost: 15.00 },
    { code: "CV", nom: "Cap-Vert", shippingCost: 14.00 },
    { code: "CF", nom: "République centrafricaine", shippingCost: 16.00 },
    { code: "CL", nom: "Chili", shippingCost: 10.50 },
    { code: "CY", nom: "Chypre", shippingCost: 7.50 },
    { code: "CO", nom: "Colombie", shippingCost: 11.00 },
    { code: "KM", nom: "Comores", shippingCost: 15.00 },
    { code: "CG", nom: "Congo", shippingCost: 15.00 },
    { code: "CD", nom: "République démocratique du Congo", shippingCost: 16.00 },
    { code: "KR", nom: "Corée du Sud", shippingCost: 6.50 },
    { code: "CR", nom: "Costa Rica", shippingCost: 12.00 },
    { code: "CI", nom: "Côte d'Ivoire", shippingCost: 14.00 },
    { code: "HR", nom: "Croatie", shippingCost: 7.00 },
    { code: "CU", nom: "Cuba", shippingCost: 15.00 },
    { code: "DK", nom: "Danemark", shippingCost: 6.00 },
    { code: "DJ", nom: "Djibouti", shippingCost: 15.00 },
    { code: "DM", nom: "Dominique", shippingCost: 13.00 },
    { code: "EG", nom: "Égypte", shippingCost: 10.00 },
    { code: "AE", nom: "Émirats arabes unis", shippingCost: 8.50 },
    { code: "EC", nom: "Équateur", shippingCost: 12.00 },
    { code: "ER", nom: "Érythrée", shippingCost: 16.00 },
    { code: "EE", nom: "Estonie", shippingCost: 6.50 },
    { code: "ET", nom: "Éthiopie", shippingCost: 15.00 },
    { code: "FJ", nom: "Fidji", shippingCost: 13.00 },
    { code: "FI", nom: "Finlande", shippingCost: 6.00 },
    { code: "GA", nom: "Gabon", shippingCost: 14.00 },
    { code: "GM", nom: "Gambie", shippingCost: 15.00 },
    { code: "GE", nom: "Géorgie", shippingCost: 10.00 },
    { code: "GH", nom: "Ghana", shippingCost: 14.00 },
    { code: "GR", nom: "Grèce", shippingCost: 6.50 },
    { code: "GD", nom: "Grenade", shippingCost: 13.00 },
    { code: "GT", nom: "Guatemala", shippingCost: 12.00 },
    { code: "GN", nom: "Guinée", shippingCost: 15.00 },
    { code: "GQ", nom: "Guinée équatoriale", shippingCost: 15.00 },
    { code: "GW", nom: "Guinée-Bissau", shippingCost: 15.00 },
    { code: "GY", nom: "Guyana", shippingCost: 14.00 },
    { code: "HT", nom: "Haïti", shippingCost: 14.00 },
    { code: "HN", nom: "Honduras", shippingCost: 13.00 },
    { code: "HU", nom: "Hongrie", shippingCost: 6.50 },
    { code: "IN", nom: "Inde", shippingCost: 8.00 },
    { code: "ID", nom: "Indonésie", shippingCost: 8.00 },
    { code: "IQ", nom: "Irak", shippingCost: 12.00 },
    { code: "IR", nom: "Iran", shippingCost: 14.00 },
    { code: "IE", nom: "Irlande", shippingCost: 6.00 },
    { code: "IS", nom: "Islande", shippingCost: 7.50 },
    { code: "IL", nom: "Israël", shippingCost: 8.50 },
    { code: "JM", nom: "Jamaïque", shippingCost: 12.00 },
    { code: "JP", nom: "Japon", shippingCost: 6.50 },
    { code: "JO", nom: "Jordanie", shippingCost: 10.00 },
    { code: "KZ", nom: "Kazakhstan", shippingCost: 10.00 },
    { code: "KE", nom: "Kenya", shippingCost: 13.00 },
    { code: "KG", nom: "Kirghizistan", shippingCost: 11.00 },
    { code: "KI", nom: "Kiribati", shippingCost: 15.00 },
    { code: "KW", nom: "Koweït", shippingCost: 9.00 },
    { code: "LA", nom: "Laos", shippingCost: 8.50 },
    { code: "LS", nom: "Lesotho", shippingCost: 15.00 },
    { code: "LV", nom: "Lettonie", shippingCost: 6.50 },
    { code: "LB", nom: "Liban", shippingCost: 11.00 },
    { code: "LR", nom: "Liberia", shippingCost: 15.00 },
    { code: "LY", nom: "Libye", shippingCost: 14.00 },
    { code: "LI", nom: "Liechtenstein", shippingCost: 8.00 },
    { code: "LT", nom: "Lituanie", shippingCost: 6.50 },
    { code: "LU", nom: "Luxembourg", shippingCost: 5.50 },
    { code: "MK", nom: "Macédoine du Nord", shippingCost: 9.50 },
    { code: "MG", nom: "Madagascar", shippingCost: 15.00 },
    { code: "MY", nom: "Malaisie", shippingCost: 7.50 },
    { code: "MW", nom: "Malawi", shippingCost: 15.00 },
    { code: "MV", nom: "Maldives", shippingCost: 12.00 },
    { code: "ML", nom: "Mali", shippingCost: 15.00 },
    { code: "MT", nom: "Malte", shippingCost: 7.00 },
    { code: "MA", nom: "Maroc", shippingCost: 10.00 },
    { code: "MU", nom: "Maurice", shippingCost: 13.00 },
    { code: "MR", nom: "Mauritanie", shippingCost: 15.00 },
    { code: "MX", nom: "Mexique", shippingCost: 9.50 },
    { code: "FM", nom: "Micronésie", shippingCost: 15.00 },
    { code: "MD", nom: "Moldavie", shippingCost: 9.50 },
    { code: "MC", nom: "Monaco", shippingCost: 5.50 },
    { code: "MN", nom: "Mongolie", shippingCost: 10.00 },
    { code: "ME", nom: "Monténégro", shippingCost: 9.50 },
    { code: "MZ", nom: "Mozambique", shippingCost: 15.00 },
    { code: "MM", nom: "Myanmar", shippingCost: 9.50 },
    { code: "NA", nom: "Namibie", shippingCost: 14.00 },
    { code: "NR", nom: "Nauru", shippingCost: 15.00 },
    { code: "NP", nom: "Népal", shippingCost: 11.00 },
    { code: "NI", nom: "Nicaragua", shippingCost: 13.00 },
    { code: "NE", nom: "Niger", shippingCost: 15.00 },
    { code: "NG", nom: "Nigéria", shippingCost: 14.00 },
    { code: "NO", nom: "Norvège", shippingCost: 6.50 },
    { code: "NZ", nom: "Nouvelle-Zélande", shippingCost: 9.00 },
    { code: "OM", nom: "Oman", shippingCost: 9.50 },
    { code: "UG", nom: "Ouganda", shippingCost: 15.00 },
    { code: "UZ", nom: "Ouzbékistan", shippingCost: 11.00 },
    { code: "PK", nom: "Pakistan", shippingCost: 10.50 },
    { code: "PW", nom: "Palaos", shippingCost: 15.00 },
    { code: "PS", nom: "Palestine", shippingCost: 11.00 },
    { code: "PA", nom: "Panama", shippingCost: 12.00 },
    { code: "PG", nom: "Papouasie-Nouvelle-Guinée", shippingCost: 14.00 },
    { code: "PY", nom: "Paraguay", shippingCost: 13.00 },
    { code: "NL", nom: "Pays-Bas", shippingCost: 5.50 },
    { code: "PE", nom: "Pérou", shippingCost: 12.00 },
    { code: "PH", nom: "Philippines", shippingCost: 8.00 },
    { code: "PL", nom: "Pologne", shippingCost: 6.00 },
    { code: "PT", nom: "Portugal", shippingCost: 6.00 },
    { code: "QA", nom: "Qatar", shippingCost: 9.50 },
    { code: "RO", nom: "Roumanie", shippingCost: 6.50 },
    { code: "RU", nom: "Russie", shippingCost: 9.00 },
    { code: "RW", nom: "Rwanda", shippingCost: 15.00 },
    { code: "KN", nom: "Saint-Kitts-et-Nevis", shippingCost: 13.00 },
    { code: "SM", nom: "Saint-Marin", shippingCost: 6.00 },
    { code: "VC", nom: "Saint-Vincent-et-les-Grenadines", shippingCost: 13.00 },
    { code: "LC", nom: "Sainte-Lucie", shippingCost: 13.00 },
    { code: "SB", nom: "Salomon", shippingCost: 15.00 },
    { code: "WS", nom: "Samoa", shippingCost: 15.00 },
    { code: "ST", nom: "Sao Tomé-et-Principe", shippingCost: 15.00 },
    { code: "SN", nom: "Sénégal", shippingCost: 14.00 },
    { code: "RS", nom: "Serbie", shippingCost: 9.00 },
    { code: "SC", nom: "Seychelles", shippingCost: 13.00 },
    { code: "SL", nom: "Sierra Leone", shippingCost: 15.00 },
    { code: "SG", nom: "Singapour", shippingCost: 7.00 },
    { code: "SK", nom: "Slovaquie", shippingCost: 6.50 },
    { code: "SI", nom: "Slovénie", shippingCost: 6.50 },
    { code: "SO", nom: "Somalie", shippingCost: 16.00 },
    { code: "SD", nom: "Soudan", shippingCost: 15.00 },
    { code: "SS", nom: "Soudan du Sud", shippingCost: 16.00 },
    { code: "LK", nom: "Sri Lanka", shippingCost: 10.00 },
    { code: "SE", nom: "Suède", shippingCost: 6.00 },
    { code: "SR", nom: "Suriname", shippingCost: 14.00 },
    { code: "SY", nom: "Syrie", shippingCost: 15.00 },
    { code: "TJ", nom: "Tadjikistan", shippingCost: 11.00 },
    { code: "TZ", nom: "Tanzanie", shippingCost: 15.00 },
    { code: "TD", nom: "Tchad", shippingCost: 16.00 },
    { code: "CZ", nom: "Tchéquie", shippingCost: 6.50 },
    { code: "TH", nom: "Thaïlande", shippingCost: 7.50 },
    { code: "TL", nom: "Timor oriental", shippingCost: 13.00 },
    { code: "TG", nom: "Togo", shippingCost: 15.00 },
    { code: "TO", nom: "Tonga", shippingCost: 15.00 },
    { code: "TT", nom: "Trinité-et-Tobago", shippingCost: 13.00 },
    { code: "TN", nom: "Tunisie", shippingCost: 10.50 },
    { code: "TM", nom: "Turkménistan", shippingCost: 12.00 },
    { code: "TR", nom: "Turquie", shippingCost: 8.00 },
    { code: "TV", nom: "Tuvalu", shippingCost: 15.00 },
    { code: "UA", nom: "Ukraine", shippingCost: 8.50 },
    { code: "UY", nom: "Uruguay", shippingCost: 12.00 },
    { code: "VU", nom: "Vanuatu", shippingCost: 15.00 },
    { code: "VA", nom: "Vatican", shippingCost: 6.00 },
    { code: "VE", nom: "Venezuela", shippingCost: 14.00 },
    { code: "VN", nom: "Viêt Nam", shippingCost: 7.50 },
    { code: "YE", nom: "Yémen", shippingCost: 14.00 },
    { code: "ZM", nom: "Zambie", shippingCost: 15.00 },
    { code: "ZW", nom: "Zimbabwe", shippingCost: 15.00 }
];

function initialiserPays() {
    const selectCountry = document.getElementById('modalCountrySelect');
    if (!selectCountry) return;

    selectCountry.innerHTML = listeDesPaysAvecFrais.map(pays => `
        <option value="${pays.code}">${pays.nom}</option>
    `).join('');
}

let currentSelectedProduct = null;

// --- 5. GESTION DE LA MODALE ---
function openProductModal(index) {
    const cachedStock = localStorage.getItem("cached_cj_stock");
    if (!cachedStock) return;
    const stock = JSON.parse(cachedStock);
    currentSelectedProduct = stock[index];

    if (!currentSelectedProduct) return;

    document.getElementById('modalTitle').innerText = currentSelectedProduct.nom || 'Produit';
    
    let rawImg = Array.isArray(currentSelectedProduct.images) ? currentSelectedProduct.images[0] : currentSelectedProduct.images;
    let imgSrc = rawImg ? `https://wsrv.nl/?url=${encodeURIComponent(rawImg)}&w=600&fit=cover` : '';
    document.getElementById('modalImg').src = imgSrc;

    document.getElementById('modalDesc').innerText = currentSelectedProduct.details || "Aucune description détaillée disponible.";

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
    const modal = document.getElementById('productModal');
    if (modal) modal.style.display = 'flex';
}

function closeProductModal() {
    const modal = document.getElementById('productModal');
    if (modal) modal.style.display = 'none';
}

function updateModalPriceAndSpecs() {
    if (!currentSelectedProduct) return;
    const variantSelect = document.getElementById('modalVariantSelect');
    const selectedIndex = variantSelect ? variantSelect.value : 0;

    let prixTab = Array.isArray(currentSelectedProduct.prix) ? currentSelectedProduct.prix : [currentSelectedProduct.prix];
    let currentPrice = parseFloat(prixTab[selectedIndex] || prixTab[0] || 0);

    const modalPrice = document.getElementById('modalPrice');
    if (modalPrice) modalPrice.innerText = currentPrice.toFixed(2) + " €";
    calculateShipping();
}

function calculateShipping() {
    const selectCountry = document.getElementById('modalCountrySelect');
    const countryCode = selectCountry ? selectCountry.value : "FR";
    const paysTrouve = listeDesPaysAvecFrais.find(p => p.code === countryCode);
    let shippingCost = paysTrouve ? paysTrouve.shippingCost : 5.50;

    const modalShippingCost = document.getElementById('modalShippingCost');
    if (modalShippingCost) modalShippingCost.innerText = shippingCost.toFixed(2);

    const variantSelect = document.getElementById('modalVariantSelect');
    const selectedIndex = variantSelect ? variantSelect.value : 0;
    let prixTab = Array.isArray(currentSelectedProduct.prix) ? currentSelectedProduct.prix : [currentSelectedProduct.prix];
    let currentPrice = parseFloat(prixTab[selectedIndex] || prixTab[0] || 0);

    let totalGlobal = currentPrice + shippingCost;
    const modalTotalCost = document.getElementById('modalTotalCost');
    if (modalTotalCost) modalTotalCost.innerText = totalGlobal.toFixed(2) + " €";
}

function checkoutWithCard() {
    alert("Redirection vers le système de paiement sécurisé...");
}

// --- 6. ÉVÉNEMENTS GLOBAUX ---
function initEventListeners() {
    // Écouteurs additionnels si nécessaire
}
