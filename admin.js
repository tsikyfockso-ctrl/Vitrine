document.getElementById('logoutBtn').addEventListener('click', function() {
    localStorage.removeItem("isAdmin");
    window.location.href = "login.html";
});

function checkAdminNotifications() {
    const inbox = document.getElementById("inbox-messages");
    if (!inbox) return;

    const data = localStorage.getItem("admin_notification");
    if (data) {
        const note = JSON.parse(data);
        inbox.innerHTML = `
            <div class="msg-item ${note.type}">
                <span><strong>Nouveau:</strong> ${note.message}</span>
                <button onclick="clearNotification()">Supprimer</button>
            </div>
        `;
    } else {
        inbox.innerHTML = '<p style="color: #888; text-align: center;">Aucun message reçu.</p>';
    }
}

function clearNotification() {
    localStorage.removeItem("admin_notification");
    checkAdminNotifications();
}

document.addEventListener('DOMContentLoaded', checkAdminNotifications);
