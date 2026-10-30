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
        
        try:
            page.goto("https://www.mujkaktus.cz/prihlaseni")
            
            # Počkáme 3 vteřiny, aby se stihly načíst případné vyskakovací lišty
            page.wait_for_timeout(3000)
            
            page.fill('input[name="jmeno"]', KAKTUS_USER)
            page.fill('input[name="heslo"]', KAKTUS_PASS)
            page.click('button:has-text("Přihlásit")')
            
            page.wait_for_selector('text="AKTUÁLNÍ STAV KREDITU"')
            page_text = page.inner_text("body")
            
            match = re.search(r'(\d+,\d+|\d+)\s*GB\s*Data', page_text)
            if match:
                hodnota_gb = match.group(1).replace(',', '.')
                hodnota_mb = int(float(hodnota_gb) * 1024)
                print(f"Nalezeno {hodnota_gb} GB, odesílám {hodnota_mb} MB.")
                requests.get(f"{MACRODROID_WEBHOOK}?zbytek={hodnota_mb}")
            else:
                print("Zůstatek nenalezen.")
                
        except Exception as e:
            print(f"Skript spadl: {e}")
            # Při chybě se vyfotí obrazovka
            page.screenshot(path="error.png")
            raise 
            
        finally:
            browser.close()

if __name__ == "__main__":
    run()
