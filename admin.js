// --- CONFIGURATION GITHUB GIST ADMIN ---
const GIST_ID = "1c09d3c6ce20fa6af040b2c235c84262";
const GITHUB_TOKEN = "VOTRE_TOKEN_GITHUB_ICI"; // ⚠️ Insérez le même Personal Access Token GitHub ici pour autoriser l'admin à modifier
const GIST_URL = "https://gist.githubusercontent.com/tsikyfockso-ctrl/1c09d3c6ce20fa6af040b2c235c84262/raw/gistfile1.txt";

document.getElementById('logoutBtn').addEventListener('click', function() {
    localStorage.removeItem("isAdmin");
    window.location.href = "login.html";
});

const modal = document.getElementById("inboxModal");

document.getElementById("inboxBtn").addEventListener("click", () => {
    modal.style.display = "flex";
    checkAdminNotifications();
});

function closeModal() {
    modal.style.display = "none";
}

document.addEventListener('DOMContentLoaded', () => {
    const paymentHistoryBtn = document.getElementById('paymentHistoryBtn');
    if (paymentHistoryBtn) {
        paymentHistoryBtn.onclick = () => {
            const paymentModal = document.getElementById('paymentHistoryModal');
            if (paymentModal) paymentModal.style.display = 'flex';
            chargerHistoriquePaiements();
        };
    }
});

function closePaymentHistoryModal() {
    const paymentModal = document.getElementById('paymentHistoryModal');
    if (paymentModal) paymentModal.style.display = 'none';
}

async function chargerHistoriquePaiements() {
    const container = document.getElementById('payment-history-list');
    if (!container) return;

    container.innerHTML = `<p style="font-size: 0.9rem; color: #777;">Chargement des paiements...</p>`;

    try {
        const response = await fetch(GIST_URL + "?v=" + new Date().getTime());
        if (!response.ok) throw new Error("Erreur de chargement du Gist");

        const data = await response.json();
        let paiements = (data && data.paiements) ? data.paiements : [];

        if (paiements.length === 0) {
            container.innerHTML = `<p style="font-size: 0.9rem; color: #777;">Aucun paiement validé pour le moment.</p>`;
            return;
        }

        let html = '';
        paiements.slice().reverse().forEach((p) => {
            html += `
                <div style="background: #e8f8f5; border-left: 4px solid #27ae60; padding: 12px; margin-bottom: 12px; border-radius: 6px; font-size: 0.90rem; display: flex; justify-content: space-between; align-items: flex-start;">
                    <div style="flex-grow: 1;">
                        <div style="font-weight: bold; color: #27ae60; font-size: 0.95rem; border-bottom: 1px solid #d0e9e1; padding-bottom: 4px; margin-bottom: 6px;">
                            💰 Paiement Reçu - ${p.date || 'Date N/A'}
                        </div>
                        <p style="margin: 2px 0; color: #2c3e50;"><strong>👤 Client :</strong> ${p.nom || 'Nom non renseigné'}</p>
                        <p style="margin: 2px 0; color: #555;"><strong>📍 Adresse :</strong> ${p.adresse || 'N/A'}, ${p.province || ''} (${p.pays || p.destination || 'N/A'})</p>
                        <p style="margin: 2px 0; color: #555;"><strong>📞 Tél :</strong> ${p.telephone || 'N/A'} | <strong>✉️ Email :</strong> ${p.email || 'N/A'}</p>
                        <p style="margin: 4px 0; color: #333;"><strong>Produit :</strong> ${p.produit || 'N/A'}</p>
                        <p style="margin: 4px 0; color: #333;"><strong>Variante :</strong> ${p.variante || 'N/A'} (SKU : ${p.sku || 'N/A'})</p>
                        <p style="margin: 4px 0; color: #333;"><strong>Quantité :</strong> ${p.quantite || '1'} | <strong>Destination :</strong> ${p.destination || 'N/A'} (Frais : ${p.fraisPort || '0 $'})</p>
                        <p style="margin: 6px 0 0 0; color: #2c3e50; font-weight: bold; font-size: 1rem;">Total réglé : ${p.total || '0 $'}</p>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    } catch (e) {
        console.error("Erreur de chargement des paiements :", e);
        container.innerHTML = `<p style="font-size: 0.9rem; color: #e74c3c;">Erreur lors du chargement de l'historique.</p>`;
    }
}

async function updateNotificationBadge() {
    try {
        const response = await fetch(GIST_URL + "?v=" + new Date().getTime());
        const data = await response.json();
        let messages = (data && data.messages) ? data.messages : [];
        
        const nonLus = messages.filter(m => m.lu === false || !m.reponse).length;
        const btn = document.getElementById("inboxBtn");
        if (btn) {
            btn.innerHTML = nonLus > 0 ? `Boîte de réception (${nonLus})` : "Boîte de réception";
            btn.style.borderColor = nonLus > 0 ? "orange" : "transparent";
        }
    } catch (e) {
        console.error("Erreur de mise à jour du badge Gist :", e);
    }
}

async function checkAdminNotifications() {
    const inbox = document.getElementById("inbox-messages");
    if (!inbox) return;

    inbox.innerHTML = "<p style='padding: 10px; color: #666;'>Chargement des messages...</p>";
    
    try {
        const response = await fetch(GIST_URL + "?v=" + new Date().getTime());
        const data = await response.json();
        let messages = (data && data.messages) ? data.messages : [];
        
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
            
            const boutonEffacer = `
                <button class="delete-btn" onclick="deleteMessage(${index})" style="background: #e74c3c; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-size: 0.85rem; margin-left: 10px;">Effacer</button>
            `;
            
            div.innerHTML = contenuHtml + boutonEffacer;
            inbox.appendChild(div);
        });
        
        updateNotificationBadge();
    } catch (e) {
        console.error("Erreur de chargement des messages Gist :", e);
        inbox.innerHTML = "<p style='padding: 10px; color: red;'>Erreur de chargement des messages.</p>";
    }
}

// 3. Envoyer la réponse de l'admin directement sur GitHub
async function envoyerReponseAdmin(index) {
    const inputReponse = document.getElementById(`admin-reply-${index}`);
    if (!inputReponse) return;
    const texteReponse = inputReponse.value.trim();

    if (!texteReponse) {
        alert("Veuillez écrire une réponse.");
        return;
    }

    try {
        const res = await fetch(`https://api.github.com/gists/${GIST_ID}`);
        if (!res.ok) throw new Error("Erreur de récupération du Gist");
        const gistData = await res.json();
        const fileName = Object.keys(gistData.files)[0];
        let donnees = JSON.parse(gistData.files[fileName].content);

        if (donnees.messages && donnees.messages[index]) {
            donnees.messages[index].reponse = texteReponse;
            donnees.messages[index].lu = true;
        }

        const updateRes = await fetch(`https://api.github.com/gists/${GIST_ID}`, {
            method: 'PATCH',
            headers: {
                'Authorization': `token ${GITHUB_TOKEN}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                files: {
                    [fileName]: {
                        content: JSON.stringify(donnees, null, 2)
                    }
                }
            })
        });

        if (updateRes.ok) {
            alert("Réponse envoyée avec succès !");
            checkAdminNotifications();
        } else {
            alert("Erreur lors de l'enregistrement de la réponse.");
        }
    } catch (e) {
        console.error("Erreur :", e);
        alert("Erreur réseau lors de l'envoi de la réponse.");
    }
}

// 4. Supprimer un message directement sur GitHub
async function deleteMessage(index) {
    if (!confirm("Voulez-vous vraiment supprimer ce message ?")) return;

    try {
        const res = await fetch(`https://api.github.com/gists/${GIST_ID}`);
        if (!res.ok) throw new Error("Erreur de récupération du Gist");
        const gistData = await res.json();
        const fileName = Object.keys(gistData.files)[0];
        let donnees = JSON.parse(gistData.files[fileName].content);

        if (donnees.messages) {
            donnees.messages.splice(index, 1);
        }

        const updateRes = await fetch(`https://api.github.com/gists/${GIST_ID}`, {
            method: 'PATCH',
            headers: {
                'Authorization': `token ${GITHUB_TOKEN}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                files: {
                    [fileName]: {
                        content: JSON.stringify(donnees, null, 2)
                    }
                }
            })
        });

        if (updateRes.ok) {
            checkAdminNotifications();
        } else {
            alert("Erreur lors de la suppression.");
        }
    } catch (e) {
        console.error("Erreur :", e);
        alert("Erreur réseau lors de la suppression.");
    }
}

function getFichierActif() {
    const select = document.getElementById('adminCategorySelect');
    if (select) {
        return select.value; 
    }
    return "update_stock.json"; 
}

function changerFichierAdmin() {
    loadStock(false);
}

let globalStockData = [];

async function loadStock(silent = false) {
    const stockList = document.getElementById("stock-list");
    if (!stockList) return;

    const fichierActif = getFichierActif();

    if (!silent && stockList.innerHTML.trim() === "") {
        stockList.innerHTML = `<p style='padding: 10px; color: #666;'>Chargement des détails du stock pour ${fichierActif}...</p>`;
    }

    try {
        const response = await fetch(fichierActif + "?v=" + new Date().getTime());
        if (!response.ok) throw new Error(`Impossible de charger ${fichierActif}`);
        
        globalStockData = await response.json();
        
        if (!Array.isArray(globalStockData) || globalStockData.length === 0) {
            if (!silent) {
                stockList.innerHTML = `<p style='padding: 10px; color: orange;'>Aucun produit trouvé dans cette catégorie (${fichierActif}).</p>`;
            }
            return;
        }

        renderStockTable();

    } catch (e) {
        console.error("Erreur lors du chargement des détails du stock :", e);
        if (!silent) {
            stockList.innerHTML = `<p style='padding: 10px; color: red;'>Erreur de chargement du fichier ${fichierActif}</p>`;
        }
    }
}

function renderStockTable() {
    const stockList = document.getElementById("stock-list");
    if (!stockList) return;

    const existingContainer = stockList.querySelector('div[style*="overflow"]');
    let savedScrollTop = 0;
    let savedScrollLeft = 0;
    if (existingContainer) {
        savedScrollTop = existingContainer.scrollTop;
        savedScrollLeft = existingContainer.scrollLeft;
    }

    const searchInput = document.getElementById("stockSearchInput");
    const searchTerm = searchInput ? searchInput.value.toLowerCase().trim() : "";

    let html = `
        <div style="max-height: 500px; overflow-y: auto; overflow-x: auto; border: 1px solid #ddd; background: #fff;">
            <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem; text-align: left; white-space: nowrap;">
                <thead style="position: sticky; top: 0; z-index: 10; background: #2c3e50; color: white;">
                    <tr>
                        <th style="padding: 10px 8px; border: 1px solid #ddd; background: #2c3e50;">Image</th>
                        <th style="padding: 10px 8px; border: 1px solid #ddd; background: #2c3e50;">Nom du Produit</th>
                        <th style="padding: 10px 8px; border: 1px solid #ddd; background: #2c3e50;">VID</th>
                        <th style="padding: 10px 8px; border: 1px solid #ddd; background: #2c3e50;">Taille</th>
                        <th style="padding: 10px 8px; border: 1px solid #ddd; background: #2c3e50;">Couleur</th>
                        <th style="padding: 10px 8px; border: 1px solid #ddd; background: #2c3e50;">SKU</th>
                        <th style="padding: 10px 8px; border: 1px solid #ddd; background: #2c3e50;">Prix ($)</th>
                        <th style="padding: 10px 8px; border: 1px solid #ddd; background: #2c3e50;">Poids (g)</th>
                        <th style="padding: 10px 8px; border: 1px solid #ddd; background: #2c3e50;">Stock</th>
                        <th style="padding: 10px 8px; border: 1px solid #ddd; background: #2c3e50;">Méthode FR</th>
                        <th style="padding: 10px 8px; border: 1px solid #ddd; background: #2c3e50;">Port FR ($)</th>
                        <th style="padding: 10px 8px; border: 1px solid #ddd; background: #2c3e50;">Méthode US</th>
                        <th style="padding: 10px 8px; border: 1px solid #ddd; background: #2c3e50;">Port US ($)</th>
                        <th style="padding: 10px 8px; border: 1px solid #ddd; background: #2c3e50;">Actions</th>
                    </tr>
                </thead>
                <tbody>
    `;

    let lignesAjoutees = 0;

    globalStockData.forEach((produit, pIndex) => {
        const nomProduit = produit.nom || "Produit sans nom";
        let rawImg = Array.isArray(produit.images) ? produit.images[0] : produit.images;
        let imgSrc = rawImg ? rawImg.trim() : "https://via.placeholder.com/40";

        if (Array.isArray(produit.variantes) && produit.variantes.length > 0) {
            produit.variantes.forEach((v) => {
                const skuVar = v.sku || '';
                const correspond = nomProduit.toLowerCase().includes(searchTerm) || skuVar.toLowerCase().includes(searchTerm);

                if (correspond) {
                    lignesAjoutees++;
                    html += `
                        <tr style="border-bottom: 1px solid #eee; background: ${lignesAjoutees % 2 === 0 ? '#f9f9f9' : '#ffffff'};">
                            <td style="padding: 6px; border: 1px solid #ddd; text-align: center;">
                                <img src="${imgSrc}" alt="" style="width: 35px; height: 35px; object-fit: cover; border-radius: 4px;">
                            </td>
                            <td style="padding: 6px; border: 1px solid #ddd; font-weight: bold; color: #333;">${nomProduit}</td>
                            <td style="padding: 6px; border: 1px solid #ddd; color: #555;">${v.vid || 'N/A'}</td>
                            <td style="padding: 6px; border: 1px solid #ddd; color: #555;">${v.taille || 'Standard'}</td>
                            <td style="padding: 6px; border: 1px solid #ddd; color: #555;">${v.couleur || 'N/A'}</td>
                            <td style="padding: 6px; border: 1px solid #ddd; font-family: monospace; font-size: 0.8rem; color: #666;">${skuVar || 'N/A'}</td>
                            <td style="padding: 6px; border: 1px solid #ddd; color: #27ae60; font-weight: bold;">${v.prix !== undefined ? v.prix + ' $' : 'N/A'}</td>
                            <td style="padding: 6px; border: 1px solid #ddd; color: #555;">${v.poids !== undefined ? v.poids + 'g' : 'N/A'}</td>
                            <td style="padding: 6px; border: 1px solid #ddd; color: #2980b9; font-weight: bold;">${v.stock !== undefined ? v.stock : 'N/A'}</td>
                            <td style="padding: 6px; border: 1px solid #ddd; color: #555; font-size: 0.8rem;">${v.shippingMethodFR || 'N/A'}</td>
                            <td style="padding: 6px; border: 1px solid #ddd; color: #e67e22;">${v.shippingCostFR !== undefined ? v.shippingCostFR + ' $' : 'N/A'}</td>
                            <td style="padding: 6px; border: 1px solid #ddd; color: #555; font-size: 0.8rem;">${v.shippingMethodUS || 'N/A'}</td>
                            <td style="padding: 6px; border: 1px solid #ddd; color: #e67e22;">${v.shippingCostUS !== undefined ? v.shippingCostUS + ' $' : 'N/A'}</td>
                            <td style="padding: 6px; border: 1px solid #ddd; text-align: center;">
                                <button onclick="removeProduct(${pIndex})" style="background: #e74c3c; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 0.75rem;">Supprimer</button>
                            </td>
                        </tr>
                    `;
                }
            });
        } else {
            const correspond = nomProduit.toLowerCase().includes(searchTerm);
            if (correspond) {
                lignesAjoutees++;
                html += `
                    <tr style="border-bottom: 1px solid #eee; background: ${lignesAjoutees % 2 === 0 ? '#f9f9f9' : '#ffffff'};">
                        <td style="padding: 6px; border: 1px solid #ddd; text-align: center;">
                            <img src="${imgSrc}" alt="" style="width: 35px; height: 35px; object-fit: cover; border-radius: 4px;">
                        </td>
                        <td style="padding: 6px; border: 1px solid #ddd; font-weight: bold; color: #333;" colspan="5">${nomProduit} (Pas de variante)</td>
                        <td style="padding: 6px; border: 1px solid #ddd; color: #27ae60; font-weight: bold;">${produit.prixBase ? produit.prixBase + ' $' : 'N/A'}</td>
                        <td style="padding: 6px; border: 1px solid #ddd;" colspan="6">N/A</td>
                        <td style="padding: 6px; border: 1px solid #ddd; text-align: center;">
                            <button onclick="removeProduct(${pIndex})" style="background: #e74c3c; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 0.75rem;">Supprimer</button>
                        </td>
                    </tr>
                `;
            }
        }
    });

    if (lignesAjoutees === 0) {
        html += `<tr><td colspan="14" style="text-align: center; padding: 15px; color: #777;">Aucun produit ou SKU trouvé pour cette recherche.</td></tr>`;
    }

    html += `
                </tbody>
            </table>
        </div>
    `;

    stockList.innerHTML = html;

    const newContainer = stockList.querySelector('div[style*="overflow"]');
    if (newContainer) {
        newContainer.scrollTop = savedScrollTop;
        newContainer.scrollLeft = savedScrollLeft;
    }
}

function filterStock() {
    renderStockTable();
}

setInterval(() => {
    if (typeof loadStock === 'function' && document.getElementById("stock-list")) {
        loadStock(true);
    }
    if (typeof updateNotificationBadge === 'function') {
        updateNotificationBadge();
    }
}, 4000);

document.addEventListener('DOMContentLoaded', () => {
    updateNotificationBadge();
    if (typeof loadStock === 'function' && document.getElementById("stock-list")) {
        loadStock(false);
    }
});
