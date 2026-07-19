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

// Fonction de vérification (inchangée)
// Fonction appelée par le bouton "Boîte de réception"
function checkAdminNotifications() {
    const inbox = document.getElementById("inbox-messages");
    const data = localStorage.getItem("admin_messages_list");
    
    if (data) {
        let messages = JSON.parse(data);
        inbox.innerHTML = ""; 
        
        messages.forEach((note, index) => {
            const div = document.createElement("div");
            div.innerHTML = `
                <div style="padding:10px; border:1px solid #ccc; margin:5px;">
                    <p><strong>${note.nom} :</strong> ${note.message}</p>
                    <button onclick="openMessageWindow(${index})">Répondre</button>
                </div>
            `;
            inbox.appendChild(div);
        });
    }
}

// Ouvrir la fenêtre de réponse
function openMessageWindow(index) {
    let messages = JSON.parse(localStorage.getItem("admin_messages_list"));
    let note = messages[index];

    const win = window.open("", "_blank", "width=400,height=400");
    win.document.write(`
        <h3>Répondre à ${note.nom}</h3>
        <textarea id="replyText" style="width:90%; height:100px;">${note.reponse || ''}</textarea><br>
        <button onclick="saveAndClose()">Envoyer</button>
        <script>
            function saveAndClose() {
                const rep = document.getElementById('replyText').value;
                window.opener.updateReply(${index}, rep);
                window.close(); // Ferme la fenêtre après clic
            }
        </script>
    `);
}

// Mise à jour et fermeture
window.updateReply = function(index, rep) {
    let messages = JSON.parse(localStorage.getItem("admin_messages_list"));
    messages[index].reponse = rep;
    localStorage.setItem("admin_messages_list", JSON.stringify(messages));
    checkAdminNotifications(); // Rafraîchir la liste admin
};
