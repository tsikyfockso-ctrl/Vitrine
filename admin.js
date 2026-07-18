document.getElementById('logoutBtn').addEventListener('click', function() {
    // Supprime la clé qui indique que l'admin est connecté
    localStorage.removeItem("isAdmin");
    
    // Redirige l'utilisateur vers la page de login
    window.location.href ="login.html";
});
function showNotification(message, type = 'success') {
    const container = document.getElementById('notification-container');
    const note = document.createElement('div');
    note.className = `notification ${type}`;
    note.innerText = message;
    
    container.appendChild(note);
    
    // Supprime la notification après 3 secondes
    setTimeout(() => {
        note.remove();
    }, 3000000);
}
// Exemple : Notification lors de la déconnexion
document.getElementById('logoutBtn').addEventListener('click', function() {
    showNotification("Déconnexion réussie...", "success");
    
    // Attendre un peu avant de rediriger pour que l'admin voie le message
    setTimeout(() => {
        localStorage.removeItem("isAdmin");
        window.location.href = "login.html";
    }, 1000);
});

// Exemple : Notification d'erreur
// showNotification("Erreur lors de la sauvegarde", "error");
