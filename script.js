// --- 1. CONFIGURATION INITIALE ---
window.onload = () => {
    loadClientMessages();
    loadProductsFromCJ();
    initEventListeners();
};

// --- 2. GESTION DES PRODUITS (API CJ DROPSHIPPING) ---
async function loadProductsFromCJ() {
    // Remplacez cette URL par votre endpoint d'API ou votre serveur intermédiaire qui communique avec CJ Dropshipping
    const url = "VOTRE_ENDPOINT_API_CJ_DROPSHIPPING"; 
    const container = document.getElementById('product-container');
    if (!container) return;

    let hasLoadedFromCache = false;

    // 1. Affichage immédiat via le cache local (pour éviter les temps de chargement)
    const cachedStock = localStorage.getItem("cached_cj_stock");
    if (cachedStock) {
        try {
            const stock = JSON.parse(cachedStock);
            if (Array.isArray(stock) && stock.length > 0) {
                renderProducts(stock, container);
                hasLoadedFromCache = true;
            }
        } catch (e) {
            localStorage.removeItem("cached_cj_stock");
        }
    }

    // 2. Si rien en cache, affichage d'un message de chargement
    if (!hasLoadedFromCache) {
        container.innerHTML = "<p style='text-align:center; width:100%; padding:20px;'>Chargement des produits depuis CJ Dropshipping...</p>";
    }

    // 3. Récupération en arrière-plan des données de l'API CJ
    try {
        const response = await fetch(url);
        const data = await response.json();
        
        // Adaptez selon la structure de retour de votre API (ex: data.products ou data directement)
        const stock = Array.isArray(data) ? data : (data.products || []);
        
        if (stock.length > 0) {
            localStorage.setItem("cached_cj_stock", JSON.stringify(stock));
            renderProducts(stock, container);
        }
    } catch (e) {
        console.error("Erreur lors de la récupération depuis l'API CJ Dropshipping:", e);
        if (!hasLoadedFromCache) {
            container.innerHTML = "<p style='text-align:center; width:100%; padding:20px; color:red;'>Impossible de charger les produits pour le moment.</p>";
        }
    }
}

// Fonction d'affichage sécurisée des produits
function renderProducts(stock, container) {
    container.innerHTML = ""; 

    stock.forEach(p => {
        // Adaptez les propriétés (p.img, p.nom, p.prix) selon le format de retour de l'API CJ
        let rawImg = p.img || p.image || p.imageUrl || ""; 
        let imgSrc = rawImg.trim();
        
        const card = document.createElement('div');
        card.className = "card product-card"; // Nécessaire pour le filtre de recherche de votre HTML
        card.style.cursor = "pointer";

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

        img.alt = p.nom || p.productName || 'Produit';
        img.loading = "lazy";

        img.onerror = function() {
            this.src = imgSrc;
            this.onerror = null; 
        };

        const title = document.createElement('h3');
        title.textContent = p.nom || p.productName || 'Sans nom';

        const price = document.createElement('p');
        price.className = "price";
        price.textContent = `${p.prix || p.sellPrice || '0'} €`;

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

    modalTitle.textContent = product.nom || product.productName || 'Sans nom';
    modalPrice.textContent = `Prix : ${product.prix || product.sellPrice || '0'} €`;
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
    const ctaBtn = document.querySelector('header button');
    if (ctaBtn) {
        ctaBtn.addEventListener('click', () => {
            const produitsSection = document.querySelector('#produits');
            if (produitsSection) {
                produitsSection.scrollIntoView({ behavior: 'smooth' });
            }
        });
    }

    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', filtrerProduits);
    }
}

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
