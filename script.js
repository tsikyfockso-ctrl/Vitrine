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

    let hasLoadedFromCache = false;

    // 1. Affichage immédiat via le cache local
    const cachedStock = localStorage.getItem("cached_aliexpress_stock");
    if (cachedStock) {
        try {
            const stock = JSON.parse(cachedStock);
            if (Array.isArray(stock) && stock.length > 0) {
                renderProducts(stock, container);
                hasLoadedFromCache = true; // On a affiché instantanément
            }
        } catch (e) {
            localStorage.removeItem("cached_aliexpress_stock");
        }
    }

    // 2. Si on n'a rien en cache, on affiche un message discret de chargement
    if (!hasLoadedFromCache) {
        container.innerHTML = "<p style='text-align:center; width:100%; padding:20px;'>Chargement des produits en cours...</p>";
    }

    // 3. Récupération en arrière-plan des données fraîches
    try {
        const response = await fetch(url);
        const stock = await response.json();
        
        if (Array.isArray(stock) && stock.length > 0) {
            // Met à jour le cache
            localStorage.setItem("cached_aliexpress_stock", JSON.stringify(stock));
            
            // On ré-affiche uniquement si le cache était vide ou obsolète
            renderProducts(stock, container);
        }
    } catch (e) {
        console.error("Erreur lors de la mise à jour depuis Google Sheets:", e);
    }
}

// Fonction d'affichage directe et sécurisée
function renderProducts(stock, container) {
    container.innerHTML = ""; 

    stock.forEach(p => {
        let rawImg = p.img || p.image || ""; 
        let imgSrc = rawImg.trim();
        
        const card = document.createElement('div');
        card.className = "card product-card";

        const imgContainer = document.createElement('div');
        imgContainer.className = "card-img-container";

        const img = document.createElement('img');
        
        if (imgSrc) {
            // Utilisation d'un proxy d'image pour contourner le blocage du navigateur
            let cleanUrl = imgSrc.replace(/^https?:\/\//, '');
            img.src = `https://images.weserv.nl/?url=${encodeURIComponent(cleanUrl)}`;
        } else {
            img.src = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='200' viewBox='0 0 300 200'><rect width='100%' height='100%' fill='%23e0e0e0'/><text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' font-family='sans-serif' font-size='16' fill='%23666'>Image Indisponible</text></svg>";
        }

        img.alt = p.nom || 'Produit';
        img.loading = "lazy";

        // Sécurité de secours : si le proxy échoue, on tente le lien direct d'origine
        img.onerror = function() {
            this.src = imgSrc;
            this.onerror = null; 
        };

        const title = document.createElement('h3');
        title.textContent = p.nom || 'Sans nom';

        const price = document.createElement('p');
        price.textContent = `Prix : ${p.prix || '0'}€`;

        const button = document.createElement('button');
        button.textContent = "Ajouter au panier";

        imgContainer.appendChild(img);
        card.appendChild(imgContainer);
        card.appendChild(title);
        card.appendChild(price);
        card.appendChild(button);

        container.appendChild(card);
    });
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
    
    const largeurCarte = 270; 
    
    if (direction === 'gauche') {
        container.scrollBy({ left: -largeurCarte, behavior: 'smooth' });
    } else {
        container.scrollBy({ left: largeurCarte, behavior: 'smooth' });
    }
}

// --- GLISSER-DÉPOSER (DRAG TO SCROLL) AVEC LA SOURIS ---
const slider = document.getElementById('product-container');
let isDown = false;
let startX;
let scrollLeft;

if (slider) {
    slider.addEventListener('mousedown', (e) => {
        isDown = true;
        slider.classList.add('active');
        startX = e.pageX - slider.offsetLeft;
        scrollLeft = slider.scrollLeft;
    });

    slider.addEventListener('mouseleave', () => {
        isDown = false;
        slider.classList.remove('active');
    });

    slider.addEventListener('mouseup', () => {
        isDown = false;
        slider.classList.remove('active');
    });

    slider.addEventListener('mousemove', (e) => {
        if (!isDown) return;
        e.preventDefault();
        const x = e.pageX - slider.offsetLeft;
        const walk = (x - startX) * 2; 
        slider.scrollLeft = scrollLeft - walk;
    });
}
