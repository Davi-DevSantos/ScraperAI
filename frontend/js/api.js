// Cliente da API (fetch). TODO: preencher endpoints conforme a API for criada.
const API_BASE = "http://localhost:8000";

const api = {
  async health() {
    const res = await fetch(`${API_BASE}/health`);
    return res.json();
  },
  // async scrape(url) { ... }
  // async analyze(content) { ... }
};