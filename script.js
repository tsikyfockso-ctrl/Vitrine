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
