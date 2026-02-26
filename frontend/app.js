const API_URL = "https://autogest-backend-ikmb.onrender.com";
const token = localStorage.getItem("token");
let veiculoIdSelecionado = null;

// Verifica se está logado
if (!token && !window.location.href.includes("index.html")) {
    window.location.href = "index.html";
}

// 1. Listar Estoque
async function listarEstoque() {
    try {
        const res = await fetch(`${API_URL}/veiculos`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        const veiculos = await res.json();
        const tbody = document.getElementById("lista-veiculos");

        if (!tbody) return; // Evita erro se não estiver na página da tabela

        tbody.innerHTML = veiculos.map(v => `
            <tr>
                <td><strong>${v.marca} ${v.modelo}</strong></td>
                <td>${v.placa}</td>
                <td>R$ ${v.valor.toLocaleString('pt-BR')}</td>
                <td>
                    <button class="btn-venda" onclick="prepararVenda(${v.id}, '${v.placa}')">✔️ Vender</button>
                    <button onclick="excluir(${v.id})" style="color:red; background:none; border:none; cursor:pointer; margin-left:10px;">🗑️</button>
                </td>
            </tr>
        `).join("");
    } catch (err) {
        console.error("Erro ao carregar veículos:", err);
    }
}

// 2. Salvar Novo (Cadastro)
async function salvarVeiculo() {
    const dados = {
        marca: document.getElementById("cadMarca").value,
        modelo: document.getElementById("cadModelo").value,
        placa: document.getElementById("cadPlaca").value.toUpperCase(),
        ano: document.getElementById("cadAno").value,
        valor: parseFloat(document.getElementById("cadValor").value)
    };

    const res = await fetch(`${API_URL}/veiculos`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify(dados)
    });

    if (res.ok) {
        fecharModal('modalCadastro');
        listarEstoque();
    }
}

// 3. Abrir Venda
function prepararVenda(id, placa) {
    veiculoIdSelecionado = id;
    document.getElementById("infoVeiculoVenda").innerText = "Placa: " + placa;
    abrirModal('modalVenda');
}

// 4. Confirmar Venda (RENAVE)
async function confirmarVenda() {
    const dados = {
        nome: document.getElementById("vendaNome").value,
        documento: document.getElementById("vendaDoc").value,
        endereco: document.getElementById("vendaEnd").value,
        valor_venda: parseFloat(document.getElementById("vendaValorFinal").value)
    };

    const res = await fetch(`${API_URL}/veiculos/${veiculoIdSelecionado}/vender`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify(dados)
    });

    if (res.ok) {
        alert("Venda concluída!");
        fecharModal('modalVenda');
        listarEstoque();
    }
}

// Auxiliares
async function excluir(id) {
    if (confirm("Excluir veículo?")) {
        await fetch(`${API_URL}/veiculos/${id}`, { method: "DELETE", headers: { "Authorization": `Bearer ${token}` } });
        listarEstoque();
    }
}

function abrirModal(id) { document.getElementById(id).style.display = "flex"; }
function fecharModal(id) { document.getElementById(id).style.display = "none"; }
function logout() { localStorage.removeItem("token"); window.location.href = "index.html"; }

// Inicialização
document.addEventListener("DOMContentLoaded", listarEstoque);