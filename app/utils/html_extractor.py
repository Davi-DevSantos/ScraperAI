from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


def format_html(html: str):
    soup = BeautifulSoup(html, 'html.parse')
    
    for tags in soup['script', 'style', 'noscript', 'iframe', 'svg', 'canvas']
        tag.decompose()

def get_html(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)

        html = page.content()
        return html