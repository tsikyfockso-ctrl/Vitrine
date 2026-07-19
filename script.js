const produits = [
    { nom: "Produit A", prix: "29€" },
    { nom: "Produit B", prix: "45€" },
    { nom: "Produit C", prix: "19€" }
];

const container = document.getElementById('product-container');

// Injection dynamique des produits
produits.forEach(p => {
    container.innerHTML += `
        <div class="card">
            <h3>${p.nom}</h3>
            <p>Prix : ${p.prix}</p>
            <button>Ajouter au panier</button>
        </div>
    `;
});

// Interaction simple
document.getElementById('cta-btn').addEventListener('click', () => {
    document.querySelector('#produits').scrollIntoView({ behavior: 'smooth' });
});
// Surveille l'apparition du bandeau Google et le supprime
const observer = new MutationObserver(() => {
    const banner = document.querySelector('.goog-te-banner-frame');
    if (banner) {
        banner.style.display = 'none';
        document.body.style.top = '0px';
    }
});

// Lance la surveillance sur tout le document
observer.observe(document.body, { childList: true, subtree: true 
});
function sendNotificationToAdmin(message, type = "info") {
    const notification = {
        message: message,
        type: type,
        timestamp: new Date().getTime()
    };
    // On enregistre dans la mémoire du navigateur
    localStorage.setItem("admin_notification", JSON.stringify(notification));
}

// Exemple : appeler cette fonction quand un client fait une action
// sendNotificationToAdmin("Un nouveau client a passé commande !", "success");

function sendComment() {
    const name = document.getElementById("userName").value;
    const msg = document.getElementById("userMsg").value;

    // Vérification : si le nom ou le message est vide, le navigateur affichera une alerte
    if (!name || !msg) {
        alert("Veuillez remplir votre nom et votre message.");
        return;
    }
    let messages = JSON.parse(localStorage.getItem("admin_messages_list") || "[]");
    
    messages.push({
        nom: name,
        message: msg,
        date: new Date().toLocaleDateString()
    });

    localStorage.setItem("admin_messages_list", JSON.stringify(messages));
    alert("Merci " + name + ", votre message a été envoyé !");
    
    // Réinitialisation
    document.getElementById("userName").value = "";
    document.getElementById("userMsg").value = "";
}
function loadClientMessages() {
    const container = document.getElementById("client-messages");
    const messages = JSON.parse(localStorage.getItem("admin_messages_list") || "[]");
    
    container.innerHTML = messages.map(m => `
        <div class="msg-card">
            <p><strong>Vous :</strong> ${m.message}</p>
            ${m.reponse ? `<p style="color:blue;"><strong>Mayah Store :</strong> ${m.reponse}</p>` : '<p><em>En attente de réponse...</em></p>'}
        </div>
    `).join('');
}
// Charger au démarrage
loadClientMessages();
