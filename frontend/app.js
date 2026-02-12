const API_URL = "https://autogest-backend-ikmb.onrender.com";
const token = localStorage.getItem("token");

// Se não tiver token, volta para o login
if (!token && !window.location.href.includes("login.html")) {
    window.location.href = "login.html";
}

// --- LÓGICA DA PÁGINA DE VEÍCULOS ---
if (window.location.href.includes("veiculos.html")) {
    const modal = document.getElementById("modalVeiculo");
    
    // Abrir/Fechar Modal
    document.getElementById("btnNovoVeiculo").onclick = () => modal.style.display = "flex";
    document.getElementById("btnCancelar").onclick = () => modal.style.display = "none";

    // Listar Veículos
    async function carregarVeiculos() {
        const res = await fetch(`${API_URL}/veiculos`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        const veiculos = await res.json();
        const lista = document.getElementById("listaVeiculos");
        lista.innerHTML = veiculos.map(v => `
            <tr>
                <td>${v.marca}</td>
                <td>${v.modelo}</td>
                <td>${v.placa}</td>
                <td>R$ ${v.valor.toLocaleString()}</td>
                <td><span class="badge">${v.status}</span></td>
            </tr>
        `).join("");
    }

    // Salvar Novo Veículo
    document.getElementById("formVeiculo").onsubmit = async (e) => {
        e.preventDefault();
        const dados = {
            marca: document.getElementById("marca").value,
            modelo: document.getElementById("modelo").value,
            placa: document.getElementById("placa").value,
            valor: parseFloat(document.getElementById("valor").value)
        };

        const res = await fetch(`${API_URL}/veiculos`, {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}` 
            },
            body: JSON.stringify(dados)
        });

        if (res.ok) {
            modal.style.display = "none";
            carregarVeiculos(); // Recarrega a lista
        }
    };

    carregarVeiculos();
}

// Botão Sair
document.getElementById("btnLogout")?.addEventListener("click", () => {
    localStorage.removeItem("token");
    window.location.href = "login.html";
});