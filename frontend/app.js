const API = "http://127.0.0.1:8000"

async function login() {
    const email = document.getElementById("email").value
    const senha = document.getElementById("senha").value

    const res = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({email, senha})
    })

    const data = await res.json()
    localStorage.setItem("token", data.access_token)
    window.location = "dashboard.html"
}

async function carregarDashboard() {
    const res = await fetch(`${API}/dashboard/`)
    const data = await res.json()

    document.getElementById("dados").innerHTML = `
        Total: ${data.total_veiculos}<br>
        Em Estoque: ${data.em_estoque}<br>
        Vendidos: ${data.vendidos}
    `
}
