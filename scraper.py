import os
import re
import requests
from playwright.sync_api import sync_playwright

KAKTUS_USER = os.getenv("KAKTUS_USER")
KAKTUS_PASS = os.getenv("KAKTUS_PASS")
MACRODROID_WEBHOOK = os.getenv("MACRODROID_WEBHOOK")

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Otevření přihlašovací stránky
        page.goto("https://www.mujkaktus.cz/prihlaseni")
        
        # Vyplnění údajů a kliknutí na přihlášení (nutno ověřit přes F12 selektory)
        page.fill('input[name="jmeno"]', KAKTUS_USER)
        page.fill('input[name="heslo"]', KAKTUS_PASS)
        page.click('button:has-text("Přihlásit")')
        
        # Čekání na načtení hlavního přehledu
        page.wait_for_selector('text="AKTUÁLNÍ STAV KREDITU"')
        page_text = page.inner_text("body")
        
        # Vyhledání vzoru jako "5,1 GB"
        match = re.search(r'(\d+,\d+|\d+)\s*GB\s*Data', page_text)
        if match:
            # Převod textu na MB
            hodnota_gb = match.group(1).replace(',', '.')
            hodnota_mb = int(float(hodnota_gb) * 1024)
            
            print(f"Nalezeno {hodnota_gb} GB, odesílám {hodnota_mb} MB do MacroDroidu.")
            requests.get(f"{MACRODROID_WEBHOOK}?zbytek={hodnota_mb}")
        else:
            print("Zůstatek dat nenalezen.")
            
        browser.close()

if __name__ == "__main__":
    run()
