// --- 1. CONFIGURATION INITIALE ---
window.onload = () => {
    loadClientMessages();
    loadProductsFromStock();
    initEventListeners();
};

// --- 2. GESTION DES PRODUITS (GOOGLE SHEETS) ---
async function loadProductsFromStock() {
    const url = "https://script.google.com/macros/s/AKfycbyOxZJjlRvmrw2U-al4CZa8ZsW4FsWwRkH9cMvRig84qqpwr0rp3lsnfpnjGjOAl8Xm/exec";
    const container = document.getElementById('product-container');
    if (!container) return;

    // 1. Charger depuis le cache pour l'affichage immédiat
    const cachedStock = localStorage.getItem("cached_aliexpress_stock");
    if (cachedStock) {
        try {
            const stock = JSON.parse(cachedStock);
            if (Array.isArray(stock) && stock.length > 0) {
                renderProducts(stock, container);
            }
        } catch (e) {
            console.error("Cache invalide, suppression...");
            localStorage.removeItem("cached_aliexpress_stock");
        }
    }

    // 2. Récupérer les données fraîches depuis Google Sheets
    try {
        const response = await fetch(url);
        const stock = await response.json();
        
        if (Array.isArray(stock)) {
            // Mettre à jour le cache proprement
            localStorage.setItem("cached_aliexpress_stock", JSON.stringify(stock));
            // Afficher les données à jour
            renderProducts(stock, container);
        }
    } catch (error) {
        console.error("Erreur de chargement des produits :", error);
        if (!cachedStock) {
            container.innerHTML = `<p style="text-align:center; width:100%; color:red;">Erreur de connexion aux produits.</p>`;
        }
    }
}

// Fonction d'affichage avec Proxy anti-blocage pour les images AliExpress
function renderProducts(stock, container) {
    container.innerHTML = stock.map(p => {
        let imgSrc = p.img && p.img.trim() !== "" ? p.img : "https://via.placeholder.com/300x200?text=Image+Indisponible";
        
        // CONTOURREMENT DU BLOCAGE ALIEXPRESS : Utilisation d'un proxy d'image sécurisé
        if (imgSrc.includes("alicdn.com") || imgSrc.includes("aliexpress")) {
            imgSrc = `https://wsrv.nl/?url=${encodeURIComponent(imgSrc)}&w=400&fit=cover`;
        }
        
        return `
            <div class="card">
                <div class="card-img-container">
                    <img src="${imgSrc}" alt="${p.nom || 'Produit'}" loading="lazy" onerror="this.src='https://via.placeholder.com/300x200?text=Erreur+Image'">
                </div>
                <h3>${p.nom || 'Sans nom'}</h3>
                <p>Prix : ${p.prix || '0'}€</p>
                <button>Ajouter au panier</button>
            </div>
        `;
    }).join('');
}

// --- 3. ÉVÉNEMENTS INTERACTIFS ---
function initEventListeners() {
    const ctaBtn = document.getElementById('cta-btn');
    if (ctaBtn) {
        ctaBtn.addEventListener('click', () => {
            const produitsSection = document.querySelector('#produits');
            if (produitsSection) {
                produitsSection.scrollIntoView({ behavior: 'smooth' });
            }
        });
    }
}

// --- 4. MESSAGERIE CLIENT ---
function toggleChat() {
    const chatPopup = document.getElementById('chat-popup');
    if (chatPopup) {
        chatPopup.classList.toggle('chat-hidden');
    }
}

function sendComment() {
    const nameInput = document.getElementById("userName");
    const msgInput = document.getElementById("userMsg");
    
    if (!nameInput.value || !msgInput.value) return alert("Veuillez remplir votre nom et message.");

    let messages = JSON.parse(localStorage.getItem("admin_messages_list") || "[]");
    messages.push({
        nom: nameInput.value,
        message: msgInput.value,
        date: new Date().toLocaleDateString(),
        reponse: "",
        lu: false
    });
    localStorage.setItem("admin_messages_list", JSON.stringify(messages));
    
    nameInput.value = "";
    msgInput.value = "";
    loadClientMessages();
}

function loadClientMessages() {
    const container = document.getElementById("client-messages");
    if (!container) return;
    const messages = JSON.parse(localStorage.getItem("admin_messages_list") || "[]");
    
    container.innerHTML = messages.map(m => `
        <div class="msg-card">
            <p><strong>${m.nom} :</strong> ${m.message}</p>
            ${m.reponse ? `<p style="color:blue;"><strong>Mayah Store :</strong> ${m.reponse}</p>` : '<p><em>En attente de réponse...</em></p>'}
        </div>
    `).join('');
}

// Rafraîchissement automatique des messages
setInterval(loadClientMessages, 2000);

// --- 5. DIVERS (Bandeau Google) ---
const observer = new MutationObserver(() => {
    const banner = document.querySelector('.goog-te-banner-frame');
    if (banner) {
        banner.style.display = 'none';
        document.body.style.top = '0px';
    }
});
observer.observe(document.body, { childList: true, subtree: true });

// --- FONCTION POUR LE DÉFILEMENT HORIZONTAL DES PRODUITS ---
function defilerProduits(direction) {
    const container = document.getElementById('product-container');
    if (!container) return;
    
    const largeurCarte = 270; // 250px (largeur de la carte) + 20px (espace 'gap')
    
    if (direction === 'gauche') {
        container.scrollBy({ left: -largeurCarte, behavior: 'smooth' });
    } else {
        container.scrollBy({ left: largeurCarte, behavior: 'smooth' });
    }
}
