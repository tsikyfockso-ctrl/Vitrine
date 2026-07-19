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

// Mise à jour du badge de notification
function updateNotificationBadge() {
    const messages = JSON.parse(localStorage.getItem("admin_messages_list") || "[]");
    const nonLus = messages.filter(m => m.lu === false).length;
    const btn = document.getElementById("inboxBtn");
    if (btn) {
        btn.innerHTML = nonLus > 0 ? `Boîte de réception (${nonLus})` : "Boîte de réception";
        btn.style.borderColor = nonLus > 0 ? "orange" : "transparent";
    }
}

// Liste des messages Admin
function checkAdminNotifications() {
    const inbox = document.getElementById("inbox-messages");
    let messages = JSON.parse(localStorage.getItem("admin_messages_list") || "[]");
    
    inbox.innerHTML = "";
    
    messages.forEach((note, index) => {
        const point = note.lu === false ? '<span style="color:orange; margin-right:10px;">●</span>' : '';
        const div = document.createElement("div");
        div.style.padding = "10px";
        div.style.borderBottom = "1px solid #eee";
        div.style.display = "flex";
        div.style.alignItems = "center";
        
        div.innerHTML = `
            <div style="display: flex; align-items: flex-start; gap: 10px; width: 100%;">
                ${point}
                <div style="flex-grow: 1;">
                    <a href="#" onclick="openMessageAndMarkRead(${index})" style="font-weight:${note.lu ? 'normal' : 'bold'}; text-decoration:none;">
                        ${note.nom}
                    </a>
                    <span style="color: #555; margin-left: 10px;">- ${note.message}</span>
                </div>
                <button class="delete-btn" onclick="deleteMessage(${index})">Effacer</button>
            </div>
        `;
        inbox.appendChild(div);
    });
}

// Ouvrir le message et marquer comme lu
function openMessageAndMarkRead(index) {
    let messages = JSON.parse(localStorage.getItem("admin_messages_list"));
    messages[index].lu = true;
    localStorage.setItem("admin_messages_list", JSON.stringify(messages));
    updateNotificationBadge();
    checkAdminNotifications();
    openMessageWindow(index);
}

// Fenêtre de réponse
function openMessageWindow(index) {
    let messages = JSON.parse(localStorage.getItem("admin_messages_list"));
    let note = messages[index];

    const win = window.open("", "_blank", "width=400,height=450");
    win.document.write(`
        <div style="padding: 20px; font-family: sans-serif;">
            <h3>Répondre à ${note.nom}</h3>
            <div style="background: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 15px;">
                <strong>Message du client :</strong><br>${note.message}
            </div>
            <textarea id="replyText" style="width:100%; height:100px;">${note.reponse || ''}</textarea><br><br>
            <button onclick="saveAndClose()">Envoyer la réponse</button>
        </div>
        <script>
            function saveAndClose() {
                const rep = document.getElementById('replyText').value;
                window.opener.updateReply(${index}, rep);
                window.close();
            }
        </script>
    `);
}

// Enregistrer la réponse
window.updateReply = function(index, rep) {
    let messages = JSON.parse(localStorage.getItem("admin_messages_list"));
    messages[index].reponse = rep;
    localStorage.setItem("admin_messages_list", JSON.stringify(messages));
    checkAdminNotifications();
};

// Suppression
function deleteMessage(index) {
    let messages = JSON.parse(localStorage.getItem("admin_messages_list") || "[]");
    messages.splice(index, 1);
    localStorage.setItem("admin_messages_list", JSON.stringify(messages));
    checkAdminNotifications();
    updateNotificationBadge();
}

// Lancer la surveillance
setInterval(updateNotificationBadge, 2000);
updateNotificationBadge();
