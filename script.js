// --- 1. CONFIGURATION INITIALE ---
window.onload = () => {
    loadClientMessages();
    loadProductsFromStock();
    initEventListeners();
};

// --- 2. GESTION DES PRODUITS (DEPUIS UPDATE_STOCK.JSON) ---
async function loadProductsFromStock() {
    const jsonUrl = "update_stock.json"; // Fichier local sur GitHub Pages
    const container = document.getElementById('product-container');
    if (!container) return;

    let hasLoadedFromCache = false;

    // 1. Cache local
    const cachedStock = localStorage.getItem("cached_mayah_stock");
    if (cachedStock) {
        try {
            const stock = JSON.parse(cachedStock);
            if (Array.isArray(stock) && stock.length > 0) {
                renderProducts(stock, container);
                hasLoadedFromCache = true;
            }
        } catch (e) {
            localStorage.removeItem("cached_mayah_stock");
        }
    }

    if (!hasLoadedFromCache) {
        container.innerHTML = "<p style='text-align:center; width:100%; padding:20px;'>Chargement des produits de Mayah Store...</p>";
    }

    // 2. Chargement de update_stock.json
    try {
        const response = await fetch(jsonUrl);
        const stock = await response.json();
        
        if (Array.isArray(stock) && stock.length > 0) {
            localStorage.setItem("cached_mayah_stock", JSON.stringify(stock));
            renderProducts(stock, container);
        }
    } catch (e) {
        console.error("Erreur lors du chargement de update_stock.json:", e);
    }
}

// Fonction d'affichage des cartes produits
function renderProducts(products, container) {
    container.innerHTML = ""; 

    products.forEach(p => {
        // Récupère la première image du tableau, ou une image par défaut
        let imgSrc = "";
        if (Array.isArray(p.images) && p.images.length > 0) {
            imgSrc = p.images[0].trim();
        }
        
        const card = document.createElement('div');
        card.className = "card product-card";
        card.style.cursor = "pointer";

        // Clic sur la carte entière pour ouvrir la modale de détails/variantes
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

        const title = document.createElement('h3');
        title.textContent = p.nom || 'Sans nom';

        const price = document.createElement('p');
        let displayPrice = (Array.isArray(p.prix) && p.prix.length > 0) ? p.prix[0] : '0';
        price.textContent = `Prix : ${displayPrice}€`;

        const button = document.createElement('button');
        button.textContent = "Voir les options";
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

// --- FONCTIONS POUR LA MODALE DE DÉTAILS ---
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
    
    // Affichage des prix et tailles multiples
    let priceText = Array.isArray(product.prix) ? product.prix.join('€ / ') + '€' : '0€';
    let sizeText = Array.isArray(product.tailles) ? product.tailles.join(', ') : 'Taille unique';

    modalPrice.innerHTML = `<strong>Prix :</strong> ${priceText}<br><strong>Tailles :</strong> ${sizeText}`;
    modalStock.textContent = `Stock disponible : ${product.stock_disponible || 0}`;
    modalDetails.textContent = product.details || 'Aucune description supplémentaire disponible.';

    modal.style.display = 'flex';
}

function closeModal() {
    const modal = document.getElementById('productModal');
    if (modal) {
        modal.style.display = 'none';
    }
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
