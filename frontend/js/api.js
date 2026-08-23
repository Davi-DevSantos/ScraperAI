const API_BASE = "http://localhost:8000";

const api = {
  async health() {
    const res = await fetch(`${API_BASE}/health`);
    return res.json();
  },
  async providers() {
    const res = await fetch(`${API_BASE}/api/providers`);
    return res.json();
  },
  
  async scrape({ url, prompt, provider, model, apiKey, maxTokens, temperature }) {
    const headers = { "Content-Type": "application/json" };
    if (apiKey) headers["X-AI-API-Key"] = apiKey;
    const body = { url, prompt };
    if (provider) body.provider = provider;
    if (model) body.model = model;
    if (apiKey) body.api_key = apiKey;
    if (maxTokens) body.max_tokens = maxTokens;
    if (temperature !== undefined && temperature !== null && temperature !== "") body.temperature = Number(temperature);
    const res = await fetch(`${API_BASE}/api/scrape`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || JSON.stringify(data));
    return data;
  },
};