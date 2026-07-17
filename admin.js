document.getElementById('logoutBtn').addEventListener('click', function() {
    // Supprime la clé qui indique que l'admin est connecté
    localStorage.removeItem("isAdmin");
    
    // Redirige l'utilisateur vers la page de login
    window.location.href ="login.html";
});
