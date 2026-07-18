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
    const data = localStorage.getItem("admin_notification");
    if (data) {
        const note = JSON.parse(data);
        inbox.innerHTML = `<div class="msg-item">${note.message} <button onclick="clearNotification()">Supprimer</button></div>`;
    } else {
        inbox.innerHTML = '<p>Aucun message.</p>';
    }
}
