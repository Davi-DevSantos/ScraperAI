console.log("AIScraper frontend carregado");

const $ = (id) => document.getElementById(id);

// Fallback local (espelha factory.AVAILABLE_MODELS) para render imediato antes do fetch
const FALLBACK_MODELS = {
  openai: ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1", "o1-mini", "o3-mini"],
  anthropic: ["claude-3-5-sonnet-latest", "claude-3-5-haiku-latest", "claude-3-opus-latest", "claude-3-haiku-20240307"],
  gemini: ["gemini-2.0-flash", "gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.5-flash-8b"],
};

let availableModels = FALLBACK_MODELS;
let defaultModels = { openai: "gpt-4o-mini", anthropic: "claude-3-5-sonnet-latest", gemini: "gemini-2.0-flash" };

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
    // repopula após fetch
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
    // inicial
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
