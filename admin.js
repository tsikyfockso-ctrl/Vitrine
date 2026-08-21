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

// ========================================================
// VOTRE CODE ORIGINAL DE GESTION DE STOCK (Intact)
// ========================================================

function addProduct() {
    const name = document.getElementById("prodName").value;
    const price = document.getElementById("prodPrice").value;
    const imgUrl = document.getElementById("prodImg").value; 
    
    if (!name || !price || !imgUrl) return alert("Veuillez remplir tous les champs (Nom, Prix, Image)");

    let stock = JSON.parse(localStorage.getItem("aliexpress_stock") || "[]");
    stock.push({ nom: name, prix: price, img: imgUrl }); 
    localStorage.setItem("aliexpress_stock", JSON.stringify(stock));
    
    document.getElementById("prodName").value = "";
    document.getElementById("prodPrice").value = "";
    document.getElementById("prodImg").value = "";
    loadStock();
}

function loadStock() {
    const stockList = document.getElementById("stock-list");
    if (!stockList) return;
    let stock = JSON.parse(localStorage.getItem("aliexpress_stock") || "[]");
    
    stockList.innerHTML = stock.map((p, index) => `
        <div style="padding: 10px; border-bottom: 1px solid #ccc;">
            ${p.nom} - ${p.prix}€ 
            <button onclick="removeProduct(${index})">Supprimer</button>
        </div>
    `).join('');
}

function removeProduct(index) {
    let stock = JSON.parse(localStorage.getItem("aliexpress_stock") || "[]");
    stock.splice(index, 1);
    localStorage.setItem("aliexpress_stock", JSON.stringify(stock));
    loadStock();
}

setInterval(updateNotificationBadge, 4000);

document.addEventListener('DOMContentLoaded', () => {
    updateNotificationBadge();
    if (typeof loadStock === 'function' && document.getElementById("stock-list")) {
        loadStock();
    }
});
