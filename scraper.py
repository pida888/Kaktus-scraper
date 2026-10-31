import os
import re
import requests
from playwright.sync_api import sync_playwright

# Přihlašovací údaje se načtou bezpečně z GitHub Secrets
KAKTUS_USER = os.getenv("KAKTUS_USER")
KAKTUS_PASS = os.getenv("KAKTUS_PASS")
MACRODROID_WEBHOOK = os.getenv("MACRODROID_WEBHOOK")

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            print("Otevírám Kaktus...")
            page.goto("https://www.mujkaktus.cz/moje-sluzby")
            page.wait_for_timeout(4000)
            
            print("Zadávám e-mail...")
            page.locator('.tm-input__input').first.fill(KAKTUS_USER, force=True)
            
            print("Zadávám heslo...")
            heslo_pole = page.locator('input[type="password"]')
            heslo_pole.fill(KAKTUS_PASS, force=True)
            print("Přihlašuji...")
            heslo_pole.press("Enter")
            
            print("Čekám na načtení samoobsluhy...")
            page.wait_for_selector('span.price.text-primary', timeout=15000)
            
            # --- EXTRAKCE DAT ---
            data_text = page.locator('.flex-equal').first.inner_text()
            matches_data = re.findall(r'(\d+,\d+|\d+)\s*GB', data_text)
            
            celkove_gb = 0.0
            for match in matches_data:
                hodnota_gb = float(match.replace(',', '.'))
                celkove_gb += hodnota_gb
                
            data_mb = int(celkove_gb * 1024)
            
            kredit_text = page.locator('span.price.text-primary').inner_text()
            match_kredit = re.search(r'(\d+)', kredit_text)
            kredit_celkem = int(match_kredit.group(1)) if match_kredit else 0
            
            bonus_celkem = 0
            bonus_locator = page.locator('details.credit-bonus-details')
            if bonus_locator.is_visible():
                bonus_text = bonus_locator.inner_text()
                match_bonus = re.search(r'hodnotě\s*(\d+)', bonus_text, re.IGNORECASE)
                if match_bonus:
                    bonus_celkem = int(match_bonus.group(1))
                    
            kredit_real = kredit_celkem - bonus_celkem
            
            print("\n--- VÝSLEDKY ---")
            print(f"Data k dispozici: {data_mb} MB ({celkove_gb} GB)")
            print(f"Kredit celkem:    {kredit_celkem} Kč")
            print(f" - Z toho bonus:  {bonus_celkem} Kč")
            print(f" - Reálný kredit: {kredit_real} Kč")
            print("----------------\n")
            
            # Odeslání do MacroDroidu s opraveným znakem &
            requests.get(f"{MACRODROID_WEBHOOK}?celkem_data={celkove_gb}&data={data_mb}&kredit={kredit_celkem}&bonus={bonus_celkem}&real={kredit_real}")

        except Exception as e:
            print(f"\nSkript spadl: {e}")
            
        finally:
            browser.close()

if __name__ == "__main__":
    run()
