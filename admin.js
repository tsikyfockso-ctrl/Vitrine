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
function checkAdminNotifications() {
    const inbox = document.getElementById("inbox-messages");
    const data = localStorage.getItem("admin_messages_list");
    
    if (data) {
        let messages = JSON.parse(data);
        messages.sort((a, b) => a.nom.localeCompare(b.nom));
        inbox.innerHTML = "";
        
        messages.forEach((note, index) => {
            const div = document.createElement("div");
            div.innerHTML = `
                <a href="#" onclick="openMessageWindow(${index})"><strong>${note.nom}</strong></a>
                <small>(${note.date})</small>
            `;
            inbox.appendChild(div);
        });
    }
}

function openMessageWindow(index) {
    let messages = JSON.parse(localStorage.getItem("admin_messages_list"));
    let note = messages[index];

    const win = window.open("", "_blank", "width=400,height=400");
    win.document.write(`
        <h3>Répondre à ${note.nom}</h3>
        <p>Message : ${note.message}</p>
        <textarea id="replyText" style="width:90%; height:100px;">${note.reponse || ''}</textarea><br>
        <button onclick="saveAndClose()">Envoyer</button>
        <script>
            function saveAndClose() {
                const rep = document.getElementById('replyText').value;
                window.opener.updateReply(${index}, rep);
                window.close();
            }
        </script>
    `);
}

window.updateReply = function(index, rep) {
    let messages = JSON.parse(localStorage.getItem("admin_messages_list"));
    messages[index].reponse = rep;
    localStorage.setItem("admin_messages_list", JSON.stringify(messages));
    checkAdminNotifications();
};
