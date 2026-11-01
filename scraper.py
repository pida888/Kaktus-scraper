import os
import re
import sys
import requests
from playwright.sync_api import sync_playwright, TimeoutError

KAKTUS_USER = os.getenv("KAKTUS_USER")
KAKTUS_PASS = os.getenv("KAKTUS_PASS")
MACRODROID_WEBHOOK = os.getenv("MACRODROID_WEBHOOK")

def run():
    if not all([KAKTUS_USER, KAKTUS_PASS, MACRODROID_WEBHOOK]):
        print("Chyba: Chybí přihlašovací údaje nebo Webhook URL v GitHub Secrets!")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Zrychlení načítání zablokováním médií
        page.route("**/*", lambda route: route.abort() 
                   if route.request.resource_type in ["image", "media", "font"] 
                   else route.continue_())
        
        try:
            print("Otevírám Kaktus...")
            page.goto("https://www.mujkaktus.cz/moje-sluzby")
            
            print("Čekám na přihlašovací pole...")
            email_pole = page.locator('.tm-input__input').first
            email_pole.wait_for(state="visible", timeout=15000)
            
            email_pole.fill(KAKTUS_USER, force=True)
            heslo_pole = page.locator('input[type="password"]')
            heslo_pole.fill(KAKTUS_PASS, force=True)
            heslo_pole.press("Enter")
            
            print("Čekám na načtení samoobsluhy...")
            page.wait_for_selector('span.price.text-primary', timeout=15000)
            
            # --- EXTRAKCE DAT (podpora pro GB i MB) ---
            data_text = page.locator('.flex-equal').first.inner_text()
            
            celkove_mb = 0
            # Nalezení hodnot v GB
            matches_gb = re.findall(r'(\d+,\d+|\d+)\s*GB', data_text, re.IGNORECASE)
            for m in matches_gb:
                celkove_mb += int(float(m.replace(',', '.')) * 1024)
                
            # Nalezení případných hodnot přímo v MB
            matches_mb = re.findall(r'(\d+,\d+|\d+)\s*MB', data_text, re.IGNORECASE)
            for m in matches_mb:
                celkove_mb += int(float(m.replace(',', '.')))
                
            celkove_gb = round(celkove_mb / 1024, 2)
            
            # --- EXTRAKCE KREDITU (ošetření mezer např. "1 250 Kč") ---
            kredit_text = page.locator('span.price.text-primary').inner_text()
            kredit_cisty = kredit_text.replace(' ', '').replace('\xa0', '')
            match_kredit = re.search(r'(\d+)', kredit_cisty)
            kredit_celkem = int(match_kredit.group(1)) if match_kredit else 0
            
            # --- BONUS KREDIT ---
            bonus_celkem = 0
            bonus_locator = page.locator('details.credit-bonus-details')
            if bonus_locator.count() > 0:
                bonus_text = bonus_locator.first.inner_text().replace(' ', '').replace('\xa0', '')
                match_bonus = re.search(r'hodnotě(\d+)', bonus_text, re.IGNORECASE)
                if match_bonus:
                    bonus_celkem = int(match_bonus.group(1))
                    
            kredit_real = kredit_celkem - bonus_celkem
            
            print("\n--- VÝSLEDKY ---")
            print(f"Data k dispozici: {celkove_mb} MB ({celkove_gb} GB)")
            print(f"Kredit celkem:    {kredit_celkem} Kč")
            print(f" - Z toho bonus:  {bonus_celkem} Kč")
            print(f" - Reálný kredit: {kredit_real} Kč")
            print("----------------\n")
            
            payload = {
                "celkem_data": celkove_gb,
                "data": celkove_mb,
                "kredit": kredit_celkem,
                "bonus": bonus_celkem,
                "real": kredit_real
            }
            # Timeout 15 sekund proti visení
            response = requests.get(MACRODROID_WEBHOOK, params=payload, timeout=15)
            
            if response.status_code == 200:
                print("Webhook úspěšně přijat.")
            else:
                print(f"Varování: MacroDroid vrátil kód {response.status_code}")

        except Exception as e:
            # Uložení snímku obrazovky pro snadné zjištění příčiny
            try:
                page.screenshot(path="error.png")
            except Exception:
                pass
            print(f"\nSkript selhal: {e}")
            sys.exit(1)
            
        finally:
            browser.close()

if __name__ == "__main__":
    run()
