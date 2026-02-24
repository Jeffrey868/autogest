const API_URL = "https://autogest-backend-ikmb.onrender.com";
const token = localStorage.getItem("token");

if (!token) window.location.href = "index.html";

// 1. Função que consulta o RENAVE e já abre o modal preenchido
async function consultarERecuperar() {
    const placa = document.getElementById("buscaPlaca").value;
    if (!placa) return alert("Digite uma placa!");

    const res = await fetch(`${API_URL}/renave/consultar/${placa}`, {
        headers: { "Authorization": `Bearer ${token}` }
    });

    if (res.ok) {
        const dados = await res.json();
        // Preenche o modal
        document.getElementById("placa").value = dados.placa;
        document.getElementById("marca").value = dados.marca;
        document.getElementById("modelo").value = dados.modelo;
        document.getElementById("ano").value = dados.ano;

        abrirModal();
    } else {
        alert("Veículo não encontrado na base de dados do governo.");
    }
}

// 2. Salvar Veículo
async function salvarVeiculo() {
    const dados = {
        placa: document.getElementById("placa").value,
        marca: document.getElementById("marca").value,
        modelo: document.getElementById("modelo").value,
        ano: document.getElementById("ano").value,
        valor: parseFloat(document.getElementById("valor").value),
        renave_numero: document.getElementById("renave_numero").value
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
        fecharModal();
        listarVeiculos();
        alert("Veículo cadastrado!");
    } else {
        alert("Erro ao salvar. Verifique se os campos estão corretos.");
    }
}

// 3. Listar na Tabela
async function listarVeiculos() {
    const res = await fetch(`${API_URL}/veiculos`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    const veiculos = await res.json();
    const tbody = document.getElementById("lista-veiculos");
    tbody.innerHTML = veiculos.map(v => `
        <tr>
            <td>${v.marca} ${v.modelo}</td>
            <td>${v.placa}</td>
            <td>${v.ano || '-'}</td>
            <td>R$ ${v.valor.toLocaleString()}</td>
            <td>
                <button onclick="excluir(${v.id})" style="background:#ff4d6d; border:none; color:white; padding:5px; border-radius:3px; cursor:pointer;">🗑️</button>
            </td>
        </tr>
    `).join("");
}

function abrirModal() { document.getElementById("modalVeiculo").style.display = "flex"; }
function fecharModal() { document.getElementById("modalVeiculo").style.display = "none"; }
function logout() { localStorage.removeItem("token"); window.location.href = "index.html"; }

// Inicializa a lista
listarVeiculos();