document.getElementById('loginForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const user = document.getElementById('username').value;
    const pass = document.getElementById('password').value;

    // ATTENTION : Ceci est une vérification basique.
    if(user === "tsikyfockso@gmail.com" && pass === "Adminserver12..") {
        localStorage.setItem("isAdmin", "true");
        window.location.href = "admin.html";
    } else {
        alert("Identifiants incorrects !");
    }
});
