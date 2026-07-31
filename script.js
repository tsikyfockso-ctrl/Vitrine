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
                hasLoadedFromCache = true;
            }
        } catch (e) {
            localStorage.removeItem("cached_aliexpress_stock");
        }
    }

    // 2. Si on n'a rien en cache, affichage d'un message de chargement
    if (!hasLoadedFromCache) {
        container.innerHTML = "<p style='text-align:center; width:100%; padding:20px;'>Chargement des produits en cours...</p>";
    }

    // 3. Récupération en arrière-plan des données fraîches
    try {
        const response = await fetch(url);
        const stock = await response.json();
        
        if (Array.isArray(stock) && stock.length > 0) {
            localStorage.setItem("cached_aliexpress_stock", JSON.stringify(stock));
            renderProducts(stock, container);
        }
    } catch (e) {
        console.error("Erreur lors de la mise à jour depuis Google Sheets:", e);
    }
}

// Fonction d'affichage directe et sécurisée des produits
function renderProducts(stock, container) {
    container.innerHTML = ""; 

    stock.forEach(p => {
        let rawImg = p.img || p.image || ""; 
        let imgSrc = rawImg.trim();
        
        const card = document.createElement('div');
        card.className = "card product-card"; // Important pour le filtre de recherche HTML
        card.style.cursor = "pointer";

        // Événement au clic sur la carte entière pour ouvrir la modale
        card.addEventListener('click', () => {
            openModal(p, imgSrc);
        });

        const imgContainer = document.createElement('div');
        imgContainer.className = "card-img-container";

        const img = document.createElement('img');
        
        if (imgSrc) {
            let cleanUrl = imgSrc.replace(/^https?:\/\//, '');
            img.src = `https://images.weserv.nl/?url=${encodeURIComponent(cleanUrl)}`;
        } else {
            img.src = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='200' viewBox='0 0 300 200'><rect width='100%' height='100%' fill='%23e0e0e0'/><text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' font-family='sans-serif' font-size='16' fill='%23666'>Image Indisponible</text></svg>";
        }

        img.alt = p.nom || 'Produit';
        img.loading = "lazy";

        img.onerror = function() {
            this.src = imgSrc;
            this.onerror = null; 
        };

        const title = document.createElement('h3');
        title.textContent = p.nom || 'Sans nom';

        const price = document.createElement('p');
        price.className = "price";
        price.textContent = `${p.prix || '0'} €`;

        const button = document.createElement('button');
        button.textContent = "Voir les détails";
        button.addEventListener('click', (e) => {
            e.stopPropagation();
            openModal(p, imgSrc);
        });

        imgContainer.appendChild(img);
        card.appendChild(imgContainer);
        card.appendChild(title);
        card.appendChild(price);
        card.appendChild(button);

        container.appendChild(card);
    });
}


// --- 3. GESTION DE LA MODALE DE DÉTAILS ---
function openModal(product, imgSrc) {
    const modal = document.getElementById('productModal');
    const modalImg = document.getElementById('modalImg');
    const modalTitle = document.getElementById('modalTitle');
    const modalPrice = document.getElementById('modalPrice');
    const modalStock = document.getElementById('modalStock');
    const modalDetails = document.getElementById('modalDetails');

    if (!modal) return;

    if (imgSrc) {
        let cleanUrl = imgSrc.replace(/^https?:\/\//, '');
        modalImg.src = `https://images.weserv.nl/?url=${encodeURIComponent(cleanUrl)}`;
    } else {
        modalImg.src = "";
    }

    modalTitle.textContent = product.nom || 'Sans nom';
    modalPrice.textContent = `Prix : ${product.prix || '0'} €`;
    modalStock.textContent = product.stock ? `Stock disponible : ${product.stock}` : '';
    modalDetails.textContent = product.description || 'Aucune description supplémentaire disponible pour ce produit.';

    modal.style.display = 'flex';
}

function closeModal() {
    const modal = document.getElementById('productModal');
    if (modal) {
        modal.style.display = 'none';
    }
}


// --- 4. ÉVÉNEMENTS INTERACTIFS & RECHERCHE ---
function initEventListeners() {
    // Bouton du header pour scroller vers les produits
    const ctaBtn = document.querySelector('header button');
    if (ctaBtn) {
        ctaBtn.addEventListener('click', () => {
            const produitsSection = document.querySelector('#produits');
            if (produitsSection) {
                produitsSection.scrollIntoView({ behavior: 'smooth' });
            }
        });
    }

    // Recherche en direct (liée à l'input de votre HTML)
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', filtrerProduits);
    }
}

// Fonction de filtrage par nom de produit
function filtrerProduits() {
    const input = document.getElementById('searchInput').value.toLowerCase();
    const cartesProduits = document.querySelectorAll('.product-card');

    cartesProduits.forEach(carte => {
        const titre = carte.querySelector('h3').textContent.toLowerCase();
        if (titre.includes(input)) {
            carte.style.display = ""; 
        } else {
            carte.style.display = "none"; 
        }
    });
}


// --- 5. MESSAGERIE CLIENT ---
function toggleChat() {
    const chatPopup = document.getElementById('chat-popup');
    if (chatPopup) {
        chatPopup.classList.toggle('chat-hidden');
    }
}

function sendComment() {
    const nameInput = document.getElementById("userName");
    const msgInput = document.getElementById("userMsg");
    
    if (!nameInput.value || !msgInput.value) {
        alert("Veuillez remplir votre nom et message.");
        return;
    }

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
        <div class="msg-card" style="background: #f9f9f9; padding: 8px; margin-bottom: 5px; border-radius: 4px; font-size: 0.9rem;">
            <p style="margin: 0;"><strong>${m.nom} :</strong> ${m.message}</p>
            ${m.reponse ? `<p style="color:blue; margin: 2px 0 0 0;"><strong>Mayah Store :</strong> ${m.reponse}</p>` : '<p style="margin: 2px 0 0 0; color: #777;"><em>En attente de réponse...</em></p>'}
        </div>
    `).join('');
}

setInterval(loadClientMessages, 3000);


// --- 6. DIVERS (Bandeau Google Traduction) ---
const observer = new MutationObserver(() => {
    const banner = document.querySelector('.goog-te-banner-frame');
    if (banner) {
        banner.style.display = 'none';
        document.body.style.top = '0px';
    }
});
observer.observe(document.body, { childList: true, subtree: true });


// --- 7. DÉFILEMENT DU CARROUSEL & DRAG TO SCROLL ---
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

// Gestion du glisser-déposer (Drag to scroll) à la souris sur le carrousel
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
