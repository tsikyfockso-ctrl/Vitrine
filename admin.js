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

// Rafraîchir le compteur de notifications toutes les 2 secondes
setInterval(updateNotificationBadge, 2000);

function updateNotificationBadge() {
    const messages = JSON.parse(localStorage.getItem("admin_messages_list") || "[]");
    const nonLus = messages.filter(m => m.lu === false).length;
    const btn = document.getElementById("inboxBtn");
    if (btn) {
        btn.innerHTML = nonLus > 0 ? `Boîte de réception (${nonLus})` : "Boîte de réception";
    }
}

function checkAdminNotifications() {
    const inbox = document.getElementById("inbox-messages");
    let messages = JSON.parse(localStorage.getItem("admin_messages_list") || "[]");
    inbox.innerHTML = "";
    messages.forEach((note, index) => {
        const point = note.lu === false ? '<span style="color:orange; margin-right:10px;">●</span>' : '';
        const div = document.createElement("div");
        div.style.padding = "10px";
        div.style.borderBottom = "1px solid #eee";
        div.innerHTML = `
          <div style="display: flex; align-items: flex-start; gap: 10px;">
            ${point} 
            <div style="flex-grow: 1;">
            <a href="#" onclick="openMessageAndMarkRead(${index})" style="font-weight:${note.lu ? 'normal' : 'bold'}; text-decoration:none;">
              ${note.nom}
            </a>
            <span style="color: #555; margin-left: 10px;">- ${note.message}</span>
            </div>
            <p style="margin: 5px 0 10px 25px; font-size: 0.9em; color: #555;">
                "${note.message}"
            </p>
            <button onclick="deleteMessage(${index})" style="margin-left: 25px;">Effacer</button>`;
        </div>
        inbox.appendChild(div);
    });
}

function openMessageAndMarkRead(index) {
    let messages = JSON.parse(localStorage.getItem("admin_messages_list"));
    messages[index].lu = true;
    localStorage.setItem("admin_messages_list", JSON.stringify(messages));
    updateNotificationBadge();
    checkAdminNotifications();
    
    // Fenêtre de réponse
    const win = window.open("", "_blank", "width=400,height=400");
    win.document.write(`<h3>Répondre à ${messages[index].nom}</h3><textarea id="rep" style="width:90%">${messages[index].reponse || ''}</textarea><br><button onclick="window.opener.updateReply(${index}, document.getElementById('rep').value); window.close()">Envoyer</button>`);
}

window.updateReply = function(index, rep) {
    let messages = JSON.parse(localStorage.getItem("admin_messages_list"));
    messages[index].reponse = rep;
    localStorage.setItem("admin_messages_list", JSON.stringify(messages));
    checkAdminNotifications();
};

function deleteMessage(index) {
    let messages = JSON.parse(localStorage.getItem("admin_messages_list") || "[]");
    messages.splice(index, 1);
    localStorage.setItem("admin_messages_list", JSON.stringify(messages));
    checkAdminNotifications();
}
