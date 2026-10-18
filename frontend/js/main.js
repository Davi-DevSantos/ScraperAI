console.log("AIScraper frontend carregado");

const $ = (id) => document.getElementById(id);

const FALLBACK_MODELS = {
  openai: ["gpt-6-astra", "gpt-6.1-sol", "gpt-6-luna", "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.4-mini", "gpt-4.1", "gpt-4o-mini"],
  anthropic: ["claude-fable-5-1", "claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5", "claude-sonnet-5", "claude-haiku-4-5"],
  gemini: ["gemini-4-argon", "gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.1-pro-preview", "gemini-3-flash-preview"],
};

let availableModels = FALLBACK_MODELS;
let defaultModels = { openai: "gpt-6-luna", anthropic: "claude-sonnet-5-5", gemini: "gemini-3.8-flash" };

function populateModelSelect(provider) {
  const modelEl = $("model");
  const helpEl = $("model-help");
  if (!modelEl) return;
  const models = availableModels[provider] || availableModels.openai;
  modelEl.innerHTML = "";
  models.forEach((m) => {
    const opt = document.createElement("option");
    opt.value = m;
    opt.textContent = m;
    if (m === defaultModels[provider]) opt.selected = true;
    modelEl.appendChild(opt);
  });
  if (helpEl) helpEl.textContent = `${models.length} modelos • default: ${defaultModels[provider] || models[0]}`;
}

async function loadProviders() {
  try {
    const data = await api.providers();
    const el = $("providers-out");
    if (el) el.textContent = JSON.stringify(data, null, 2);
    if (data.available_models) availableModels = data.available_models;
    if (data.default_models) defaultModels = data.default_models;
    const prov = $("provider")?.value || "openai";
    populateModelSelect(prov);
  } catch (e) {
    console.warn("Falha ao carregar providers", e);
    const out = $("providers-out");
    if (out) out.textContent = JSON.stringify({ available_models: availableModels, default_models: defaultModels }, null, 2);
  }
}

async function checkHealth() {
  const out = $("health-out");
  try {
    const data = await api.health();
    if (out) out.textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    if (out) out.textContent = "Erro: " + e.message;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadProviders();
  const providerEl = $("provider");
  const btnHealth = $("btn-health");
  if (btnHealth) btnHealth.addEventListener("click", checkHealth);
  if (providerEl) {
    populateModelSelect(providerEl.value || "openai");
    providerEl.addEventListener("change", () => populateModelSelect(providerEl.value));
  }

  const form = $("scrape-form");
  const resultEl = $("result");
  const statusEl = $("status");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const url = $("url").value.trim();
    const prompt = $("prompt").value.trim();
    const provider = $("provider").value;
    const model = $("model").value;
    const apiKey = $("apiKey").value.trim();
    const maxTokens = $("maxTokens").value ? Number($("maxTokens").value) : undefined;
    const temperature = $("temperature").value !== "" ? Number($("temperature").value) : undefined;

    if (!provider || !model || !apiKey) {
      if (statusEl) statusEl.textContent = "Preencha provedor, modelo e API Key";
      return;
    }

    if (statusEl) statusEl.textContent = "Carregando...";
    if (resultEl) resultEl.textContent = "";

    try {
      const data = await api.scrape({ url, prompt, provider, model, apiKey, maxTokens, temperature });
      if (statusEl) statusEl.textContent = `OK — provider: ${data.provider} | model: ${data.model}`;
      if (resultEl) {
        try {
          const parsed = JSON.parse(data.data);
          resultEl.textContent = JSON.stringify(parsed, null, 2);
        } catch {
          resultEl.textContent = data.data;
        }
      }
    } catch (err) {
      if (statusEl) statusEl.textContent = "Erro";
      if (resultEl) resultEl.textContent = err.message;
    }
  });
});