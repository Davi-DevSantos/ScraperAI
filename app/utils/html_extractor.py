import random
import time

from bs4 import BeautifulSoup, Comment
from playwright.sync_api import sync_playwright

from app.core.config import setting

# UA padrão caso .env não defina
DEFAULT_UA = setting.SCRAPER_USER_AGENT or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Args para modo silencioso + bypass de detecção
STEALTH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-dev-shm-usage",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-infobars",
    "--window-size=1920,1080",
    "--start-maximized",
    "--disable-extensions",
    "--disable-gpu",
    "--disable-features=IsolateOrigins,site-per-process",
    "--disable-web-security",
]

# Script stealth: esconde webdriver, plugins, chrome, languages
STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
Object.defineProperty(navigator, 'languages', { get: () => ['pt-BR','pt','en-US','en'] });
window.chrome = { runtime: {} };
Object.defineProperty(navigator, 'permissions', {
  get: () => ({ query: () => Promise.resolve({ state: 'granted' }) })
});
"""


def format_html(html: str):
    soup = BeautifulSoup(html, "html.parser")
    # remove tags inúteis + comentários
    for tag in soup.find_all(["script", "style", "noscript", "iframe", "svg", "canvas", "form", "button"]):
        tag.decompose()
    # comentários
    for c in soup.find_all(string=lambda text: isinstance(text, Comment)):
        c.extract()
    # remove elementos com id/classe suspeitos de captcha/antibot (mantém conteúdo útil)
    for el in soup.select("[id*='captcha'], [class*='captcha'], [id*='cf-challenge'], [class*='cf-challenge']"):
        # não remove conteúdo principal, só marca; se for container grande de challenge, remove
        if el.get_text(strip=True) and len(el.get_text(strip=True)) < 500:
            el.decompose()
    return soup


def _is_antibot_challenge(html: str) -> bool:
    low = html.lower()
    indicators = [
        "cf-challenge",
        "cloudflare",
        "just a moment",
        "attention required",
        "captcha",
        "hcaptcha",
        "recaptcha",
        "turnstile",
        "checking if the site connection is secure",
    ]
    return any(ind in low for ind in indicators)


def get_html(url: str, timeout: int | None = None) -> str:
    """Obtém HTML com Playwright em modo silencioso + bypass antibot.

    - headless silencioso
    - stealth args + init script
    - bypass_csp, viewport real, locale pt-BR, user-agent do .env
    - espera networkidle com fallback, rola página para trigger lazy-load
    - detecta challenge/captcha e tenta aguardar/recarregar 1x
    """
    t = timeout or setting.SCRAPER_TIMEOUT
    timeout_ms = t * 1000

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=STEALTH_ARGS,
        )
        context = browser.new_context(
            user_agent=DEFAULT_UA,
            viewport={"width": 1920, "height": 1080},
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
            bypass_csp=True,
            ignore_https_errors=True,
            extra_http_headers={
                "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        # bloqueia recursos pesados para acelerar e reduzir detecção (opcional)
        # context.route("**/*.{png,jpg,jpeg,webp,gif,woff,woff2,mp4}", lambda r: r.abort()) # não bloqueia por padrão para manter layout

        page = context.new_page()
        # stealth
        page.add_init_script(STEALTH_SCRIPT)
        # header extra
        page.set_extra_http_headers({"DNT": "1"})

        try:
            # goto silencioso sem log
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            # jitter humano
            time.sleep(random.uniform(0.8, 1.6))
            # tenta networkidle sem falhar se timeout (muitos sites mantêm polling)
            try:
                page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass

            # scroll suave para carregar lazy content
            try:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
                time.sleep(random.uniform(0.4, 0.8))
                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(0.3)
            except Exception:
                pass

            html = page.content()

            # detecta challenge antibot/captcha e tenta aguardar 1 recarregamento
            if _is_antibot_challenge(html):
                # espera um pouco (cloudflare 5s) e tenta re-extrair
                time.sleep(random.uniform(4.0, 6.0))
                try:
                    page.wait_for_load_state("networkidle", timeout=5000)
                except Exception:
                    pass
                html = page.content()
                # se ainda challenge, retorna mesmo assim (LLM pode lidar), mas log implícito

            return html
        finally:
            try:
                context.close()
            except Exception:
                pass
            try:
                browser.close()
            except Exception:
                pass
