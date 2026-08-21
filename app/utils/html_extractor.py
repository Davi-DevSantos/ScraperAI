from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


def format_html(html: str):
    soup = BeautifulSoup(html, 'html.parser')
    
    for tags in soup.find_all(['script', 'style', 'noscript', 'iframe', 'svg', 'canvas']):
        tags.decompose()
    return soup

def get_html(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)

        html = page.content()
        return html