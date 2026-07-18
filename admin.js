document.getElementById('logoutBtn').addEventListener('click', function() {
    // Supprime la clé qui indique que l'admin est connecté
    localStorage.removeItem("isAdmin");
    
    // Redirige l'utilisateur vers la page de login
    window.location.href ="login.html";
});
function checkAdminNotifications() {
    const data = localStorage.getItem("admin_notification");
    if (data) {
        const note = JSON.parse(data);
        const inbox = document.getElementById("inbox-messages");
        
        // Créer l'élément de message
        const div = document.createElement("div");
        div.className = `msg-item ${note.type}`;
        div.innerHTML = `<strong>Nouveau:</strong> ${note.message} <button onclick="clearNotification()">Supprimer</button>`;
        
        inbox.appendChild(div);
    }
}

function clearNotification() {
    localStorage.removeItem("admin_notification");
    document.getElementById("inbox-messages").innerHTML = "";
}

// Lancer la vérification au chargement de la page admin
window.onload = checkAdminNotifications;
