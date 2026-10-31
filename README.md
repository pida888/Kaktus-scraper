# 🌵 Kaktus Data Scraper

Automatizovaný Python skript využívající Playwright pro pravidelné stahování aktuálního stavu dat a kreditu ze samoobsluhy mobilního operátora Kaktus. Skript je navržen pro neviditelný běh v cloudu přes GitHub Actions a naměřené hodnoty odesílá prostřednictvím Webhooku do aplikace MacroDroid. Odtud se data předávají k dynamickému zobrazení na domovské obrazovce pomocí KLWP.

## ✨ Funkce
* **Chytré přihlášení:** Obchází SSO přesměrování a blokující cookies lišty odesláním formuláře přes klávesu Enter.
* **Komplexní extrakce:** Získává hodnotu zbývajících dat (v MB i GB) a provádí výpočet celkového, bonusového a reálného kreditu.
* **Automatizace:** Skript běží nezávisle na zařízení každý den ve 03:00 ráno pomocí cron úlohy v GitHub Actions.
* **Webhook integrace:** Formátuje zjištěná data jako URL parametry a odesílá je na koncový bod MacroDroidu v telefonu.

## ⚙️ Požadavky pro lokální testování
* Python 3.11+
* Knihovny: `playwright`, `requests`
* Jádro Playwright: `playwright install chromium`

## 🚀 Nastavení (GitHub Actions)
Tento projekt je připraven pro nasazení do GitHub Actions. Nikdy nevkládej přihlašovací údaje přímo do kódu.

1. V repozitáři přejdi do **Settings** -> **Secrets and variables** -> **Actions**.
2. Vytvoř následující tajné proměnné (New repository secret):
   * `KAKTUS_USER`: Tvůj přihlašovací e-mail na mujkaktus.cz.
   * `KAKTUS_PASS`: Tvé heslo.
   * `MACRODROID_WEBHOOK`: Unikátní URL adresa Webhook spouštěče z MacroDroidu.
3. Zajisti, že repozitář obsahuje spouštěcí soubor workflow (např. `.github/workflows/scraper.yml`).

## 📱 Návaznost na Android (MacroDroid & KLWP)
Tento repozitář je pouze serverová (extrakční) část. Pro plnou funkčnost na telefonu je potřeba:
1. **MacroDroid:** Makro se spouštěčem **Webhook (URL)**, které přijme URL parametry (`data`, `celkem_data`, `kredit`, `bonus`, `real`), uloží je do slovníku a pošle do KLWP pomocí akce **Tasker/Locale Plugin (Kustom Send Variable)**.
2. **Dynamický odpočet:** Aby se přes den šetřila baterie a zbytečně se nestahovala nová data z webu, noční scraping poskytuje pevný referenční bod. KLWP tapeta se pak stará o matematický výpočet aktuálního stavu odečtením lokální denní spotřeby (měřené MacroDroidem).

**Příklad finálního KLWP vzorce na ploše:**
`$if(gv(kredit), "Bonus: " + br(tasker, bonus) + " Kč", "Zbývá: " + mu(round, (br(tasker, data_MB) - br(tasker, data)) / 1024, 2) + " GB")$`