// Remplacez votre ancienne injection de produits statiques par ceci :
async function loadProductsFromStock() {
const url = "https://script.google.com/macros/s/AKfycbyOxZJjlRvmrw2U-al4CZa8ZsW4FsWwRkH9cMvRig84qqpwr0rp3lsnfpnjGjOAl8Xm/exec";
const container = document.getElementById('product-container');
try {
const response = await fetch(url);
const stock = await response.json();
container.innerHTML = stock.map(p => `

${p.nom}

Prix : ${p.prix}€

Ajouter au panier

`).join('');
} catch (error) {
console.error("Erreur de chargement :", error);
}
}

// Appeler cette fonction au chargement de index.html
window.onload = () => {
    loadClientMessages();
    loadProductsFromStock();
};

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

// Charger les messages au démarrage de la page
window.onload = loadClientMessages;
// Rafraîchissement automatique toutes les 2 secondes
setInterval(loadClientMessages, 2000);

function sendComment() {
    const name = document.getElementById("userName").value;
    const msg = document.getElementById("userMsg").value;
    if (!name || !msg) return alert("Remplissez tout");

    let messages = JSON.parse(localStorage.getItem("admin_messages_list") || "[]");
    messages.push({
        nom: name,
        message: msg,
        date: new Date().toLocaleDateString(),
        reponse: "",
        lu: false
    });
    localStorage.setItem("admin_messages_list", JSON.stringify(messages));
    document.getElementById("userName").value = "";
    document.getElementById("userMsg").value = "";
    loadClientMessages();
}

function loadClientMessages() {
    const container = document.getElementById("client-messages");
    if (!container) return;
    const messages = JSON.parse(localStorage.getItem("admin_messages_list") || "[]");
    container.innerHTML = messages.map(m => `
        <div class="msg-card">
            <p><strong>${m.nom} :</strong> ${m.message}</p>
            ${m.reponse ? `<p style="color:blue;"><strong>Mayah Store :</strong> ${m.reponse}</p>` : '<p><em>En attente...</em></p>'}
        </div>
    `).join('');
}
