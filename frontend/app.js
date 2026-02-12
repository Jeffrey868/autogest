// 1. Substituímos o localhost pelo link oficial do seu Render
const API = "https://autogest-backend-ikmb.onrender.com";

async function login() {
    const email = document.getElementById("email").value;
    const senha = document.getElementById("senha").value;

    try {
        const res = await fetch(`${API}/auth/login`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({email, senha})
        });

        if (!res.ok) throw new Error("Usuário ou senha inválidos");

        const data = await res.json();
        // Guardamos o token para usar nas próximas chamadas
        localStorage.setItem("token", data.access_token);
        window.location = "dashboard.html";
    } catch (error) {
        alert(error.message);
    }
}

async function carregarDashboard() {
    const token = localStorage.getItem("token"); // Pegamos o token salvo

    const res = await fetch(`${API}/dashboard/`, {
        method: "GET",
        headers: {
            "Authorization": `Bearer ${token}`, // Enviamos o token para o backend liberar o acesso
            "Content-Type": "application/json"
        }
    });

    if (res.status === 401) {
        window.location = "login.html"; // Se o token for inválido, volta para o login
        return;
    }

    const data = await res.json();

    document.getElementById("dados").innerHTML = `
        Total: ${data.total_veiculos}<br>
        Em Estoque: ${data.em_estoque}<br>
        Vendidos: ${data.vendidos}
    `;
}