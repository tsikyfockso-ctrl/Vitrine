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
            try {
                const stock = JSON.parse(cachedStock);
                renderProducts(stock, container);
                return;
            } catch (e) {}
        }
        
        container.innerHTML = `
            <div style="text-align:center; width:100%; padding:20px; color:red;">
                <p><strong>Impossible de charger le catalogue.</strong></p>
                <p>Vérifiez que le fichier <code>update_stock.json</code> est bien à la racine.</p>
            </div>`;
    }
}

// --- 3. AFFICHAGE DES PRODUITS ---
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

// --- 4. LISTE MONDIALE DE TOUS LES PAYS ---
const listeDesPaysAvecFrais = [
    { code: "FR", nom: "France" }, { code: "DE", nom: "Allemagne" }, { code: "BE", nom: "Belgique" },
    { code: "CH", nom: "Suisse" }, { code: "CA", nom: "Canada" }, { code: "US", nom: "États-Unis" },
    { code: "GB", nom: "Royaume-Uni" }, { code: "ES", nom: "Espagne" }, { code: "IT", nom: "Italie" },
    { code: "CN", nom: "Chine" }, { code: "AF", nom: "Afghanistan" }, { code: "AL", nom: "Albanie" },
    { code: "DZ", nom: "Algérie" }, { code: "AD", nom: "Andorre" }, { code: "AO", nom: "Angola" },
    { code: "AG", nom: "Antigua-et-Barbuda" }, { code: "SA", nom: "Arabie saoudite" }, { code: "AR", nom: "Argentine" },
    { code: "AM", nom: "Arménie" }, { code: "AU", nom: "Australie" }, { code: "AT", nom: "Autriche" },
    { code: "AZ", nom: "Azerbaïdjan" }, { code: "BS", nom: "Bahamas" }, { code: "BH", nom: "Bahreïn" },
    { code: "BD", nom: "Bangladesh" }, { code: "BB", nom: "Barbade" }, { code: "BZ", nom: "Belize" },
    { code: "BJ", nom: "Bénin" }, { code: "BT", nom: "Bhoutan" }, { code: "BY", nom: "Biélorussie" },
    { code: "BO", nom: "Bolivie" }, { code: "BA", nom: "Bosnie-Herzégovine" }, { code: "BW", nom: "Botswana" },
    { code: "BR", nom: "Brésil" }, { code: "BN", nom: "Brunéi" }, { code: "BG", nom: "Bulgarie" },
    { code: "BF", nom: "Burkina Faso" }, { code: "BI", nom: "Burundi" }, { code: "KH", nom: "Cambodge" },
    { code: "CM", nom: "Cameroun" }, { code: "CV", nom: "Cap-Vert" }, { code: "CF", nom: "République centrafricaine" },
    { code: "CL", nom: "Chili" }, { code: "CY", nom: "Chypre" }, { code: "CO", nom: "Colombie" },
    { code: "KM", nom: "Comores" }, { code: "CG", nom: "Congo" }, { code: "CD", nom: "République démocratique du Congo" },
    { code: "KR", nom: "Corée du Sud" }, { code: "CR", nom: "Costa Rica" }, { code: "CI", nom: "Côte d'Ivoire" },
    { code: "HR", nom: "Croatie" }, { code: "CU", nom: "Cuba" }, { code: "DK", nom: "Danemark" },
    { code: "DJ", nom: "Djibouti" }, { code: "DM", nom: "Dominique" }, { code: "EG", nom: "Égypte" },
    { code: "AE", nom: "Émirats arabes unis" }, { code: "EC", nom: "Équateur" }, { code: "ER", nom: "Érythrée" },
    { code: "EE", nom: "Estonie" }, { code: "ET", nom: "Éthiopie" }, { code: "FJ", nom: "Fidji" },
    { code: "FI", nom: "Finlande" }, { code: "GA", nom: "Gabon" }, { code: "GM", nom: "Gambie" },
    { code: "GE", nom: "Géorgie" }, { code: "GH", nom: "Ghana" }, { code: "GR", nom: "Grèce" },
    { code: "GD", nom: "Grenade" }, { code: "GT", nom: "Guatemala" }, { code: "GN", nom: "Guinée" },
    { code: "GQ", nom: "Guinée équatoriale" }, { code: "GW", nom: "Guinée-Bissau" }, { code: "GY", nom: "Guyana" },
    { code: "HT", nom: "Haïti" }, { code: "HN", nom: "Honduras" }, { code: "HU", nom: "Hongrie" },
    { code: "IN", nom: "Inde" }, { code: "ID", nom: "Indonésie" }, { code: "IQ", nom: "Irak" },
    { code: "IR", nom: "Iran" }, { code: "IE", nom: "Irlande" }, { code: "IS", nom: "Islande" },
    { code: "IL", nom: "Israël" }, { code: "JM", nom: "Jamaïque" }, { code: "JP", nom: "Japon" },
    { code: "JO", nom: "Jordanie" }, { code: "KZ", nom: "Kazakhstan" }, { code: "KE", nom: "Kenya" },
    { code: "KG", nom: "Kirghizistan" }, { code: "KI", nom: "Kiribati" }, { code: "KW", nom: "Koweït" },
    { code: "LA", nom: "Laos" }, { code: "LS", nom: "Lesotho" }, { code: "LV", nom: "Lettonie" },
    { code: "LB", nom: "Liban" }, { code: "LR", nom: "Liberia" }, { code: "LY", nom: "Libye" },
    { code: "LI", nom: "Liechtenstein" }, { code: "LT", nom: "Lituanie" }, { code: "LU", nom: "Luxembourg" },
    { code: "MK", nom: "Macédoine du Nord" }, { code: "MG", nom: "Madagascar" }, { code: "MY", nom: "Malaisie" },
    { code: "MW", nom: "Malawi" }, { code: "MV", nom: "Maldives" }, { code: "ML", nom: "Mali" },
    { code: "MT", nom: "Malte" }, { code: "MA", nom: "Maroc" }, { code: "MU", nom: "Maurice" },
    { code: "MR", nom: "Mauritanie" }, { code: "MX", nom: "Mexique" }, { code: "FM", nom: "Micronésie" },
    { code: "MD", nom: "Moldavie" }, { code: "MC", nom: "Monaco" }, { code: "MN", nom: "Mongolie" },
    { code: "ME", nom: "Monténégro" }, { code: "MZ", nom: "Mozambique" }, { code: "MM", nom: "Myanmar" },
    { code: "NA", nom: "Namibie" }, { code: "NR", nom: "Nauru" }, { code: "NP", nom: "Népal" },
    { code: "NI", nom: "Nicaragua" }, { code: "NE", nom: "Niger" }, { code: "NG", nom: "Nigéria" },
    { code: "NO", nom: "Norvège" }, { code: "NZ", nom: "Nouvelle-Zélande" }, { code: "OM", nom: "Oman" },
    { code: "UG", nom: "Ouganda" }, { code: "UZ", nom: "Ouzbékistan" }, { code: "PK", nom: "Pakistan" },
    { code: "PW", nom: "Palaos" }, { code: "PS", nom: "Palestine" }, { code: "PA", nom: "Panama" },
    { code: "PG", nom: "Papouasie-Nouvelle-Guinée" }, { code: "PY", nom: "Paraguay" }, { code: "NL", nom: "Pays-Bas" },
    { code: "PE", nom: "Pérou" }, { code: "PH", nom: "Philippines" }, { code: "PL", nom: "Pologne" },
    { code: "PT", nom: "Portugal" }, { code: "QA", nom: "Qatar" }, { code: "RO", nom: "Roumanie" },
    { code: "RU", nom: "Russie" }, { code: "RW", nom: "Rwanda" }, { code: "KN", nom: "Saint-Kitts-et-Nevis" },
    { code: "SM", nom: "Saint-Marin" }, { code: "VC", nom: "Saint-Vincent-et-les-Grenadines" }, { code: "LC", nom: "Sainte-Lucie" },
    { code: "SB", nom: "Salomon" }, { code: "WS", nom: "Samoa" }, { code: "ST", nom: "Sao Tomé-et-Principe" },
    { code: "SN", nom: "Sénégal" }, { code: "RS", nom: "Serbie" }, { code: "SC", nom: "Seychelles" },
    { code: "SL", nom: "Sierra Leone" }, { code: "SG", nom: "Singapour" }, { code: "SK", nom: "Slovaquie" },
    { code: "SI", nom: "Slovénie" }, { code: "SO", nom: "Somalie" }, { code: "SD", nom: "Soudan" },
    { code: "SS", nom: "Soudan du Sud" }, { code: "LK", nom: "Sri Lanka" }, { code: "SE", nom: "Suède" },
    { code: "SR", nom: "Suriname" }, { code: "SY", nom: "Syrie" }, { code: "TJ", nom: "Tadjikistan" },
    { code: "TZ", nom: "Tanzanie" }, { code: "TD", nom: "Tchad" }, { code: "CZ", nom: "Tchéquie" },
    { code: "TH", nom: "Thaïlande" }, { code: "TL", nom: "Timor oriental" }, { code: "TG", nom: "Togo" },
    { code: "TO", nom: "Tonga" }, { code: "TT", nom: "Trinité-et-Tobago" }, { code: "TN", nom: "Tunisie" },
    { code: "TM", nom: "Turkménistan" }, { code: "TR", nom: "Turquie" }, { code: "TV", nom: "Tuvalu" },
    { code: "UA", nom: "Ukraine" }, { code: "UY", nom: "Uruguay" }, { code: "VU", nom: "Vanuatu" },
    { code: "VA", nom: "Vatican" }, { code: "VE", nom: "Venezuela" }, { code: "VN", nom: "Viêt Nam" },
    { code: "YE", nom: "Yémen" }, { code: "ZM", nom: "Zambie" }, { code: "ZW", nom: "Zimbabwe" }
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

// --- 6. CALCUL AUTOMATIQUE DU PORT PAR PRODUIT & PAR PAYS MONDIAL ---
function calculateShipping() {
    const selectCountry = document.getElementById('modalCountrySelect');
    const countryCode = selectCountry ? selectCountry.value : "FR";
    
    // Attribution automatique d'un coefficient selon la zone géographique mondiale
    let multiplicateurPays = 1.0; 
    const zonesLoin = ["US", "CA", "AR", "BR", "MX", "AU", "NZ", "JP", "KR", "CN", "ZA", "AE"];
    const zonesTresLoin = ["RE", "MG", "NC", "PF", "VU", "FJ", "MU"];

    if (zonesTresLoin.includes(countryCode)) {
        multiplicateurPays = 2.2;
    } else if (zonesLoin.includes(countryCode)) {
        multiplicateurPays = 1.5;
    }

    // Récupération de la base de port propre au produit (générée par Python) ou 4.00€ par défaut
    let shippingBaseProduit = currentSelectedProduct && currentSelectedProduct.shippingBase !== undefined 
        ? parseFloat(currentSelectedProduct.shippingBase) 
        : 4.00;

    // Calcul final : Base du produit x Coefficient du pays
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

function initEventListeners() {
    // Écouteurs globaux supplémentaires si besoin
}
