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
// Attend que l'image soit chargée
    const logoImg = document.querySelector('.logo-container img');
    logoImg.addEventListener('load', function() {
        // Crée un canvas pour analyser les pixels
        const canvas = document.createElement('canvas');
        canvas.width = this.width;
        canvas.height = this.height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(this, 0, 0);
        
        // Récupère la couleur du pixel central
        const pixel = ctx.getImageData(this.width/2, this.height/2, 1, 1).data;
        const color = `rgb(${pixel[0]}, ${pixel[1]}, ${pixel[2]})`;
        
        // Applique la couleur au nav
        document.querySelector('nav').style.backgroundColor = color;
    });
