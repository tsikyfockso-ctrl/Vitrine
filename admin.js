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

// Affiche le compteur de messages non lus sur le bouton Admin
function updateNotificationBadge() {
    const messages = JSON.parse(localStorage.getItem("admin_messages_list") || "[]");
    const nonLus = messages.filter(m => m.lu === false).length;
    const btn = document.getElementById("inboxBtn");
    
    if (nonLus > 0) {
        btn.innerHTML = `Boîte de réception (${nonLus})`;
        btn.style.borderColor = "orange"; // Indique visuellement qu'il y a du nouveau
    } else {
        btn.innerHTML = `Boîte de réception`;
    }
    
// Fonction de vérification (inchangée)
// Fonction appelée par le bouton "Boîte de réception"
function checkAdminNotifications() {
    const inbox = document.getElementById("inbox-messages");
    const data = localStorage.getItem("admin_messages_list");
    
    if (data) {
        let messages = JSON.parse(data);
        inbox.innerHTML = ""; 
        
        // Remplacez votre boucle forEach actuelle par ceci pour inclure le bouton :
        messages.forEach((note, index) => {
          const div = document.createElement("div");
          div.className = "msg-item";
            
            // Point orange si non lu
          const point = note.lu === false ? '<span style="color:orange; font-size:20px; margin-right:10px;">●</span>' : '';
          div.style.display = "flex";
          div.style.alignItems = "center"; 
          div.style.padding = "10px";
          div.style.borderBottom = "1px solid #eee";
            
          div.innerHTML = `
          ${point}
            <a href="#" onclick="openMessageAndMarkRead(${index})" style="font-weight:${note.lu ? 'normal' : 'bold'}">
                ${note.nom}
            </a>
         <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; border-bottom: 1px solid #eee;">
            <a href="#" onclick="openMessageWindow('${index}')" style="font-weight:bold;">${note.nom}
            </a>
            <button class="delete-btn" onclick="deleteMessage(${index})">Effacer</button>
        </div>
    `;
         inbox.appendChild(div);
     });
   }
}
    
// Marquer comme lu quand on ouvre
function openMessageAndMarkRead(index) {
    let messages = JSON.parse(localStorage.getItem("admin_messages_list"));
    messages[index].lu = true; // Marquer comme lu
    localStorage.setItem("admin_messages_list", JSON.stringify(messages));
    updateNotificationBadge(); // Met à jour le compteur
    openMessageWindow(index); // Ouvre la fenêtre de réponse
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

function deleteMessage(index) {
    if (confirm("Voulez-vous vraiment supprimer ce message ?")) {
        let messages = JSON.parse(localStorage.getItem("admin_messages_list") || "[]");
        messages.splice(index, 1); // Retire l'objet à l'index donné
        localStorage.setItem("admin_messages_list", JSON.stringify(messages));
        checkAdminNotifications(); // Rafraîchit l'affichage
        alert("Message supprimé.");
    }
}

// Mise à jour et fermeture
window.updateReply = function(index, rep) {
    let messages = JSON.parse(localStorage.getItem("admin_messages_list"));
    messages[index].reponse = rep;
    localStorage.setItem("admin_messages_list", JSON.stringify(messages));
    checkAdminNotifications(); // Rafraîchir la liste admin
};
