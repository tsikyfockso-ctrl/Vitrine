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

    // A. AFFICHAGE INSTANTANÉ DEPUIS LE CACHE (si disponible)
    const cachedStock = localStorage.getItem("cached_aliexpress_stock");
    if (cachedStock) {
        const stock = JSON.parse(cachedStock);
        renderProducts(stock, container);
    } else {
        // Sinon, afficher un message de chargement rapide
        container.innerHTML = `<p style="text-align:center; width:100%; grid-column: 1/-1;">Chargement des produits en cours...</p>`;
    }

    // B. CHARGEMENT EN ARRIÈRE-PLAN DEPUIS GOOGLE SHEETS
    try {
        const response = await fetch(url);
        const stock = await response.json();
        
        // Sauvegarde dans le cache du navigateur pour la prochaine fois
        localStorage.setItem("cached_aliexpress_stock", JSON.stringify(stock));
        
        // Rafraîchir l'affichage avec les données fraîches
        renderProducts(stock, container);
    } catch (error) {
        console.error("Erreur de chargement des produits :", error);
        if (!cachedStock) {
            container.innerHTML = `<p style="text-align:center; width:100%; color:red;">Impossible de charger les produits pour le moment.</p>`;
        }
    }
}

// Fonction utilitaire pour éviter de répéter le code HTML des cartes
function renderProducts(stock, container) {
    container.innerHTML = stock.map(p => `
        <div class="card">
            <div class="card-img-container">
                <img src="${p.img}" alt="${p.nom}">
            </div>
            <h3>${p.nom}</h3>
            <p>Prix : ${p.prix}€</p>
            <button>Ajouter au panier</button>
        </div>
    `).join('');
}
// --- 3. ÉVÉNEMENTS INTERACTIFS (Correction erreur null) ---
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
