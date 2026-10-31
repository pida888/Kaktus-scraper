import os
import re
import requests
from playwright.sync_api import sync_playwright, TimeoutError

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
            
            # Místo pevného čekání (hard sleep) se dynamicky čeká, až bude pole pro e-mail viditelné
            print("Čekám na načtení přihlašovacího formuláře...")
            email_pole = page.locator('.tm-input__input').first
            email_pole.wait_for(state="visible", timeout=15000)
            
            print("Zadávám e-mail...")
            email_pole.fill(KAKTUS_USER, force=True)
            
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
            
            # Bezpečnější kontrola, zda element na stránce vůbec existuje, než se z něj čte text
            if bonus_locator.count() > 0:
                bonus_text = bonus_locator.first.inner_text()
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
            
            # Odeslání do MacroDroidu a ověření HTTP statusu
            url = f"{MACRODROID_WEBHOOK}?celkem_data={celkove_gb}&data={data_mb}&kredit={kredit_celkem}&bonus={bonus_celkem}&real={kredit_real}"
            response = requests.get(url)
            
            if response.status_code == 200:
                print("Úspěšně odesláno přes Webhook do MacroDroidu.")
            else:
                print(f"Chyba při odesílání do MacroDroidu. HTTP Status: {response.status_code}")

        # Specifické odchytávání chyb pro snazší diagnostiku v GitHub Actions logu
        except TimeoutError:
            print("\nSkript spadl: TimeoutError - Prvek se nenačetl včas (možná změna CSS tříd na webu Kaktusu nebo pomalé spojení).")
        except Exception as e:
            print(f"\nSkript spadl: {e}")
            
        finally:
            browser.close()

if __name__ == "__main__":
    run()
