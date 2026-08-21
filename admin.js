// --- CONFIGURATION CLOUD (Récupérée depuis config.js et les secrets) ---
const BIN_ID = (typeof window !== 'undefined' && window.CONFIG_BIN_ID) ? window.CONFIG_BIN_ID : "6a86df44f5f4af5e292ca904"; 
const API_KEY = (typeof window !== 'undefined' && window.CONFIG_API_KEY) ? window.CONFIG_API_KEY : "$2a$10$oWpiZV8hm0i.OzlsyPjBSOjhcp7i/oia15o2pK4d7ZWNXSdE3Piva"; 
const URL_API = `https://api.jsonbin.io/v3/b/${BIN_ID}`;

document.getElementById('logoutBtn').addEventListener('click', function() {
    localStorage.removeItem("isAdmin");
    window.location.href = "login.html";
});

const modal = document.getElementById("inboxModal");

// Ouvrir la boîte
document.getElementById("inboxBtn").addEventListener("click", () => {
    modal.style.display = "flex";
    checkAdminNotifications();
});

// Fermer la boîte
function closeModal() {
    modal.style.display = "none";
}

// 1. Mise à jour du badge de notification (depuis JSONbin.io)
async function updateNotificationBadge() {
    try {
        const response = await fetch(URL_API + "/latest", {
            headers: { 'X-Master-Key': API_KEY }
        });
        const data = await response.json();
        let messages = (data.record && data.record.messages) ? data.record.messages : [];
        
        const nonLus = messages.filter(m => m.lu === false || !m.reponse).length;
        const btn = document.getElementById("inboxBtn");
        if (btn) {
            btn.innerHTML = nonLus > 0 ? `Boîte de réception (${nonLus})` : "Boîte de réception";
            btn.style.borderColor = nonLus > 0 ? "orange" : "transparent";
        }
    } catch (e) {
        console.error("Erreur de mise à jour du badge :", e);
    }
}

// 2. Liste des messages Admin (récupérés depuis le cloud JSONbin.io avec le bouton Effacer)
async function checkAdminNotifications() {
    const inbox = document.getElementById("inbox-messages");
    if (!inbox) return;
    
    inbox.innerHTML = "<p style='padding: 10px; color: #666;'>Chargement des messages...</p>";
    
    try {
        const response = await fetch(URL_API + "/latest", {
            headers: { 'X-Master-Key': API_KEY }
        });
        const data = await response.json();
        let messages = (data.record && data.record.messages) ? data.record.messages : [];
        
        inbox.innerHTML = "";
        
        if (messages.length === 0) {
            inbox.innerHTML = "<p style='padding: 10px; color: #666;'>Aucun message reçu pour le moment.</p>";
            return;
        }
        
        messages.forEach((note, index) => {
            const aRepondu = note.reponse && note.reponse.trim() !== "";
            const point = (note.lu === false || !aRepondu) ? '<span style="color:orange; margin-right:10px;">●</span>' : '';
            const clientNom = note.nom ? note.nom : "Client Anonyme";
            
            const div = document.createElement("div");
            div.style.padding = "10px";
            div.style.borderBottom = "1px solid #eee";
            div.style.marginBottom = "8px";
            div.style.display = "flex";
            div.style.alignItems = "flex-start";
            div.style.justifyContent = "space-between";
            
            let contenuHtml = `
                <div style="flex-grow: 1;">
                    <div>${point}<strong>👤 ${clientNom} :</strong> ${note.message}</div>
            `;
            
            if (aRepondu) {
                contenuHtml += `
                    <div style="margin-top: 5px; margin-left: 20px; font-size: 0.9rem; color: #27ae60; background: #e8f8f5; padding: 6px; border-radius: 4px;">
                        <strong>Votre réponse :</strong> ${note.reponse}
                    </div>
                `;
            } else {
                contenuHtml += `
                    <div style="margin-top: 8px; margin-left: 20px;">
                        <input type="text" id="admin-reply-${index}" placeholder="Écrire une réponse..." style="width: 70%; padding: 5px; border: 1px solid #ccc; border-radius: 4px;">
                        <button onclick="envoyerReponseAdmin(${index})" style="background: #27ae60; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; margin-left: 5px;">Répondre</button>
                    </div>
                `;
            }
            
            contenuHtml += `</div>`;
            
            // Bouton Effacer moderne
            const boutonEffacer = `
                <button class="delete-btn" onclick="deleteMessage(${index})" style="background: #e74c3c; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-size: 0.85rem; margin-left: 10px;">Effacer</button>
            `;
            
            div.innerHTML = contenuHtml + boutonEffacer;
            inbox.appendChild(div);
        });
        
        updateNotificationBadge();
    } catch (e) {
        console.error("Erreur de chargement des messages admin :", e);
        inbox.innerHTML = "<p style='padding: 10px; color: red;'>Erreur de chargement des messages.</p>";
    }
}

// 3. Fonction pour envoyer la réponse de l'admin vers le cloud
async function envoyerReponseAdmin(index) {
    const inputReponse = document.getElementById(`admin-reply-${index}`);
    if (!inputReponse) return;
    
    const texteReponse = inputReponse.value.trim();
    if (!texteReponse) {
        alert("Veuillez écrire une réponse.");
        return;
    }
    
    try {
        const getRes = await fetch(URL_API + "/latest", {
            headers: { 'X-Master-Key': API_KEY }
        });
        const data = await getRes.json();
        let messages = (data.record && data.record.messages) ? data.record.messages : [];
        
        if (messages[index]) {
            messages[index].reponse = texteReponse;
            messages[index].lu = true;
        }
        
        await fetch(URL_API, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-Master-Key': API_KEY
            },
            body: JSON.stringify({ messages: messages })
        });
        
        alert("Réponse envoyée avec succès !");
        checkAdminNotifications(); 
    } catch (e) {
        console.error("Erreur lors de l'envoi de la réponse :", e);
        alert("Erreur lors de l'envoi de la réponse.");
    }
}

// 4. Fonction pour supprimer un message du cloud
async function deleteMessage(index) {
    if (!confirm("Voulez-vous vraiment supprimer ce message ?")) return;
    
    try {
        const getRes = await fetch(URL_API + "/latest", {
            headers: { 'X-Master-Key': API_KEY }
        });
        const data = await getRes.json();
        let messages = (data.record && data.record.messages) ? data.record.messages : [];
        
        // Supprime le message ciblée
        messages.splice(index, 1);
        
        // Sauvegarde la liste mise à jour sur JSONbin.io
        await fetch(URL_API, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-Master-Key': API_KEY
            },
            body: JSON.stringify({ messages: messages })
        });
        
        checkAdminNotifications();
        updateNotificationBadge();
    } catch (e) {
        console.error("Erreur lors de la suppression du message :", e);
        alert("Erreur lors de la suppression.");
    }
}

// --- FONCTION POUR CHARGER ET AFFICHER LE STOCK (Façon Tableau Excel) ---
// --- FONCTION POUR CHARGER ET AFFICHER LE STOCK AVEC TOUS LES DÉTAILS ---
async function loadStock() {
    const stockList = document.getElementById("stock-list");
    if (!stockList) return;

    stockList.innerHTML = "<p style='padding: 10px; color: #666;'>Chargement des détails du stock...</p>";

    try {
        const response = await fetch("update_stock.json?v=" + new Date().getTime());
        if (!response.ok) throw new Error("Impossible de charger update_stock.json");
        
        const stock = await response.json();
        
        if (!Array.isArray(stock) || stock.length === 0) {
            stockList.innerHTML = `<p style='padding: 10px; color: orange;'>Aucun produit trouvé dans le stock.</p>`;
            return;
        }

        // Tableau complet avec toutes vos colonnes demandées
        let html = `
            <div style="overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse; background: #fff; font-size: 0.85rem; text-align: left; white-space: nowrap;">
                    <thead>
                        <tr style="background: #2c3e50; color: white;">
                            <th style="padding: 8px; border: 1px solid #ddd;">Image</th>
                            <th style="padding: 8px; border: 1px solid #ddd;">Nom du Produit</th>
                            <th style="padding: 8px; border: 1px solid #ddd;">VID</th>
                            <th style="padding: 8px; border: 1px solid #ddd;">Taille</th>
                            <th style="padding: 8px; border: 1px solid #ddd;">Couleur</th>
                            <th style="padding: 8px; border: 1px solid #ddd;">SKU</th>
                            <th style="padding: 8px; border: 1px solid #ddd;">Prix (€)</th>
                            <th style="padding: 8px; border: 1px solid #ddd;">Poids (g)</th>
                            <th style="padding: 8px; border: 1px solid #ddd;">Stock</th>
                            <th style="padding: 8px; border: 1px solid #ddd;">Méthode FR</th>
                            <th style="padding: 8px; border: 1px solid #ddd;">Port FR (€)</th>
                            <th style="padding: 8px; border: 1px solid #ddd;">Méthode US</th>
                            <th style="padding: 8px; border: 1px solid #ddd;">Port US (€)</th>
                            <th style="padding: 8px; border: 1px solid #ddd;">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        stock.forEach((produit, pIndex) => {
            const nomProduit = produit.nom || "Produit sans nom";
            let rawImg = Array.isArray(produit.images) ? produit.images[0] : produit.images;
            let imgSrc = rawImg ? rawImg.trim() : "https://via.placeholder.com/40";

            if (Array.isArray(produit.variantes) && produit.variantes.length > 0) {
                produit.variantes.forEach((v, vIndex) => {
                    html += `
                        <tr style="border-bottom: 1px solid #eee; background: ${pIndex % 2 === 0 ? '#f9f9f9' : '#ffffff'};">
                            <td style="padding: 6px; border: 1px solid #ddd; text-align: center;">
                                <img src="${imgSrc}" alt="" style="width: 35px; height: 35px; object-fit: cover; border-radius: 4px;">
                            </td>
                            <td style="padding: 6px; border: 1px solid #ddd; font-weight: bold; color: #333;">${nomProduit}</td>
                            <td style="padding: 6px; border: 1px solid #ddd; color: #555;">${v.vid || 'N/A'}</td>
                            <td style="padding: 6px; border: 1px solid #ddd; color: #555;">${v.taille || 'Standard'}</td>
                            <td style="padding: 6px; border: 1px solid #ddd; color: #555;">${v.couleur || 'N/A'}</td>
                            <td style="padding: 6px; border: 1px solid #ddd; font-family: monospace; font-size: 0.8rem; color: #666;">${v.sku || 'N/A'}</td>
                            <td style="padding: 6px; border: 1px solid #ddd; color: #27ae60; font-weight: bold;">${v.prix !== undefined ? v.prix + ' €' : 'N/A'}</td>
                            <td style="padding: 6px; border: 1px solid #ddd; color: #555;">${v.poids !== undefined ? v.poids : 'N/A'}</td>
                            <td style="padding: 6px; border: 1px solid #ddd; color: #2980b9; font-weight: bold;">${v.stock !== undefined ? v.stock : 'N/A'}</td>
                            <td style="padding: 6px; border: 1px solid #ddd; color: #555; font-size: 0.8rem;">${v.shippingMethodFR || 'N/A'}</td>
                            <td style="padding: 6px; border: 1px solid #ddd; color: #e67e22;">${v.shippingCostFR !== undefined ? v.shippingCostFR + ' €' : 'N/A'}</td>
                            <td style="padding: 6px; border: 1px solid #ddd; color: #555; font-size: 0.8rem;">${v.shippingMethodUS || 'N/A'}</td>
                            <td style="padding: 6px; border: 1px solid #ddd; color: #e67e22;">${v.shippingCostUS !== undefined ? v.shippingCostUS + ' €' : 'N/A'}</td>
                            <td style="padding: 6px; border: 1px solid #ddd; text-align: center;">
                                <button onclick="removeProduct(${pIndex})" style="background: #e74c3c; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 0.75rem;">Supprimer</button>
                            </td>
                        </tr>
                    `;
                });
            } else {
                // S'il n'y a pas de variantes
                html += `
                    <tr style="border-bottom: 1px solid #eee; background: ${pIndex % 2 === 0 ? '#f9f9f9' : '#ffffff'};">
                        <td style="padding: 6px; border: 1px solid #ddd; text-align: center;">
                            <img src="${imgSrc}" alt="" style="width: 35px; height: 35px; object-fit: cover; border-radius: 4px;">
                        </td>
                        <td style="padding: 6px; border: 1px solid #ddd; font-weight: bold; color: #333;" colspan="5">${nomProduit} (Pas de variante)</td>
                        <td style="padding: 6px; border: 1px solid #ddd; color: #27ae60; font-weight: bold;">${produit.prixBase ? produit.prixBase + ' €' : 'N/A'}</td>
                        <td style="padding: 6px; border: 1px solid #ddd;" colspan="6">N/A</td>
                        <td style="padding: 6px; border: 1px solid #ddd; text-align: center;">
                            <button onclick="removeProduct(${pIndex})" style="background: #e74c3c; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 0.75rem;">Supprimer</button>
                        </td>
                    </tr>
                `;
            }
        });

        html += `
                    </tbody>
                </table>
            </div>
        `;

        stockList.innerHTML = html;

    } catch (e) {
        console.error("Erreur lors du chargement des détails du stock :", e);
        stockList.innerHTML = `<p style='padding: 10px; color: red;'>Erreur de chargement du fichier update_stock.json</p>`;
    }
}

// Actualiser automatiquement le tableau des stocks toutes les 4 secondes
setInterval(() => {
    if (typeof loadStock === 'function' && document.getElementById("stock-list")) {
        loadStock();
    }
}, 4000);

// Charger le stock dès l'ouverture de la page admin
document.addEventListener('DOMContentLoaded', () => {
    updateNotificationBadge();
    if (typeof loadStock === 'function' && document.getElementById("stock-list")) {
        loadStock();
    }
});
