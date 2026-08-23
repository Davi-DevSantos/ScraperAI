import random
import time

from bs4 import BeautifulSoup, Comment
from playwright.sync_api import sync_playwright

from app.core.config import setting

DEFAULT_UA = setting.SCRAPER_USER_AGENT or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

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
    for tag in soup.find_all(["script", "style", "noscript", "iframe", "svg", "canvas", "form", "button"]):
        tag.decompose()
    for c in soup.find_all(string=lambda text: isinstance(text, Comment)):
        c.extract()
    for el in soup.select("[id*='captcha'], [class*='captcha'], [id*='cf-challenge'], [class*='cf-challenge']"):
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


def _launch_browser(p):
    for name in ("chromium", "firefox", "webkit"):
        try:
            browser_type = getattr(p, name)
            return browser_type.launch(headless=True, args=STEALTH_ARGS)
        except Exception:
            continue
    return p.chromium.launch(headless=True, args=STEALTH_ARGS)


def get_html(url: str, timeout: int | None = None) -> str:
    t = timeout or setting.SCRAPER_TIMEOUT
    timeout_ms = t * 1000
    with sync_playwright() as p:
        browser = _launch_browser(p)
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
        page = context.new_page()
        page.add_init_script(STEALTH_SCRIPT)
        page.set_extra_http_headers({"DNT": "1"})
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            time.sleep(random.uniform(0.8, 1.6))
            try:
                page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass
            try:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
                time.sleep(random.uniform(0.4, 0.8))
                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(0.3)
            except Exception:
                pass
            html = page.content()
            if _is_antibot_challenge(html):
                time.sleep(random.uniform(4.0, 6.0))
                try:
                    page.wait_for_load_state("networkidle", timeout=5000)
                except Exception:
                    pass
                html = page.content()
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
