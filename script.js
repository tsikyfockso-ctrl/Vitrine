// --- 1. CONFIGURATION INITIALE ---
window.onload = () => {
    loadClientMessages();
    loadProductsFromCJJson();
    initEventListeners();
};

// --- 2. GESTION DES PRODUITS (DEPUIS LE JSON CJ DROPSHIPPING) ---
async function loadProductsFromCJJson() {
    const jsonUrl = "update_stock.json"; // Fichiers généré automatiquement par Python/GitHub Actions
    const container = document.getElementById('product-container');
    if (!container) return;

    // 1. Affichage depuis le cache local pour aller vite
    const cachedStock = localStorage.getItem("cached_cj_stock");
    if (cachedStock) {
        try {
            const stock = JSON.parse(cachedStock);
            if (Array.isArray(stock) && stock.length > 0) {
                renderProducts(stock, container);
            }
        } catch (e) {
            localStorage.removeItem("cached_cj_stock");
        }
    }

    // 2. Récupération du fichier JSON mis à jour
    try {
        const response = await fetch(jsonUrl);
        const stock = await response.json();
        
        if (Array.isArray(stock)) {
            localStorage.setItem("cached_cj_stock", JSON.stringify(stock));
            renderProducts(stock, container);
        }
    } catch (error) {
        console.error("Erreur de chargement du catalogue CJ :", error);
        if (!cachedStock) {
            container.innerHTML = `<p style="text-align:center; width:100%; color:red;">Impossible de charger les produits.</p>`;
        }
    }
}

// Fonction d'affichage adaptée à la structure de CJ Dropshipping
function renderProducts(stock, container) {
    container.innerHTML = stock.map(p => {
        // Récupération de la première image disponible dans le tableau d'images CJ
        let rawImg = "";
        if (Array.isArray(p.images) && p.images.length > 0) {
            rawImg = p.images.find(img => img && img.trim() !== "") || "";
        } else if (typeof p.images === "string") {
            rawImg = p.images;
        }

        let imgSrc = rawImg.trim() !== "" ? rawImg : "https://via.placeholder.com/300x200?text=Image+Indisponible";
        
        // Proxy anti-blocage si l'image vient d'un CDN tiers/Ali/CJ
        if (imgSrc.includes("alicdn.com") || imgSrc.includes("cj") || imgSrc.includes("aliexpress")) {
            imgSrc = `https://wsrv.nl/?url=${encodeURIComponent(imgSrc)}&w=400&fit=cover`;
        }

        // Récupération du premier prix du tableau de prix CJ
        let prixAffiche = "0";
        if (Array.isArray(p.prix) && p.prix.length > 0) {
            prixAffiche = p.prix[0] || "0";
        } else {
            prixAffiche = p.prix || "0";
        }
        
        return `
            <div class="card">
                <div class="card-img-container">
                    <img src="${imgSrc}" alt="${p.nom || 'Produit'}" loading="lazy" onerror="this.src='https://via.placeholder.com/300x200?text=Erreur+Image'">
                </div>
                <h3>${p.nom || 'Sans nom'}</h3>
                <p>Prix : ${prixAffiche} €</p>
                <button>Ajouter au panier</button>
            </div>
        `;
    }).join('');
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
