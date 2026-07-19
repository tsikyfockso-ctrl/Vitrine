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
    // On récupère la liste complète des messages (supposons qu'ils soient stockés dans "admin_messages_list")
    const data = localStorage.getItem("admin_messages_list");
    
    if (data) {
        let messages = JSON.parse(data);
        
        // 1. Tri par nom alphabétique
        messages.sort((a, b) => a.nom.localeCompare(b.nom));
        
        inbox.innerHTML = ""; // Vider la liste
        
        messages.forEach((note, index) => {
            const div = document.createElement("div");
            div.className = "msg-item";
            
            // 2. Création du lien qui ouvre le message dans une nouvelle fenêtre
            div.innerHTML = `
                <a href="#" onclick="openMessageWindow('${index}')" style="font-weight:bold; cursor:pointer;">
                    ${note.nom}
                </a> 
                <small>(${note.date})</small>
            `;
            inbox.appendChild(div);
        });
    } else {
        inbox.innerHTML = '<p>Aucun message.</p>';
    }
}

// Fonction pour ouvrir une nouvelle fenêtre
function openMessageWindow(index) {
    let messages = JSON.parse(localStorage.getItem("admin_messages_list"));
    let note = messages[index];

    const win = window.open("", "_blank", "width=400,height=400");
    win.document.write(`
        <h3>Message de ${note.nom}</h3>
        <p><strong>Client :</strong> ${note.message}</p>
        <hr>
        <textarea id="replyText" placeholder="Votre réponse...">${note.reponse || ''}</textarea><br>
        <button onclick="saveReply(${index})">Envoyer la réponse</button>
        <script>
            function saveReply(idx) {
                const rep = document.getElementById('replyText').value;
                window.opener.updateReply(idx, rep);
                window.close();
            }
        </script>
    `);
}

// Fonction appelée par la fenêtre éphémère pour mettre à jour le stockage
window.updateReply = function(index, rep) {
    let messages = JSON.parse(localStorage.getItem("admin_messages_list"));
    messages[index].reponse = rep;
    localStorage.setItem("admin_messages_list", JSON.stringify(messages));
    alert("Réponse enregistrée !");
};
