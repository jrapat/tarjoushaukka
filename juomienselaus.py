import json
import os
import re
import subprocess
from playwright.sync_api import sync_playwright

# Tarkistetaan automaattisesti, ajetaanko skriptiä GitHub Actionsissa (CI) vai omalla koneella
is_ci = os.getenv("CI") is not None

# Päivitetty etäisyyssanakirja Tuusulasta (km yhdensuuntaisesti)
TUUSULA_DISTANCES = {
    "Hyrrä": 1,
    "Hyrylä": 1,
    "Lahela": 3,
    "Sahankulma": 4,
    "Parila": 5,
    "Järvenpää": 10,
    "Kinnari": 10,
    "Kyrölä": 10,
    "Saunakallio": 10,
    "Pajala": 11,
    "Kerava": 12,
    "Karuselli": 12,
    "Keravan asema": 12,
    "Kalevantori": 12,
    "Ahjontori": 12,
    "Haarajoki": 13,
    "Satukallio": 13,
    "Kellokoski": 14,
    "Kivistö": 14,
    "Jokela": 20,
    "Pornainen": 28,
    "Mäntsälä": 32,
    "Lähde": 22,
    "Rajamäki": 22,
    "Klaukkala": 22,
    "Nurmijärvi": 20,
    "Masi": 20,
    "Röykkä": 28,
    "Karppala": 25,
    "Nummela": 45,
    "Karkkila": 55,
    "Lohja": 45,
    "Kirkkonummi": 48,
    "Korso": 15,
    "Nikinmäki": 15,
    "Hakunila": 15,
    "Ilola": 15,
    "Kulomäki": 15,
    "Mikkola": 16,
    "Rekola": 16,
    "Oregano": 16,
    "Asola": 17,
    "Koivukylä": 17,
    "Tammisto": 18,
    "Jumbo": 18,
    "Tikkuri": 18,
    "Dixi": 18,
    "Kielotie": 18,
    "Jokiniemi": 18,
    "Simonkallio": 18,
    "Peltola": 18,
    "Yliveto": 18,
    "Riskiläkuja": 18,
    "Kastanja": 18,
    "Kartanonkoski": 18,
    "Ristipuro": 18,
    "Ylästö": 16,
    "Manteli": 20,
    "Honkatori": 22,
    "Martsari": 21,
    "Martinlaakson Ostari": 21,
    "Martinlaakso": 21,
    "Myyrmäki": 22,
    "Myyrvalinta": 22,
    "Louhela": 22,
    "Niipperi": 22,
    "Länsimäki": 22,
    "Pähkinärinne": 25,
    "Hämeenkylä": 24,
    "Pähkinä": 24,
    "Puistori": 20,
    "Heikinlaakso": 20,
    "Suutarila": 20,
    "Tapuli": 20,
    "Siltamäki": 21,
    "Töyrynummi": 21,
    "Torpparinmäki": 21,
    "Jakomäki": 22,
    "Viikki": 23,
    "Myllypuro": 24,
    "Vesala": 24,
    "Pukinmäki": 22,
    "Savela": 22,
    "Pikkusisko": 22,
    "Mustapekka": 25,
    "Konala": 25,
    "Kontumarket": 25,
    "Easton": 25,
    "Columbus": 25,
    "Basilika": 25,
    "Pohjois-Haaga": 26,
    "Haaga": 26,
    "Reimarla": 26,
    "Hertta": 26,
    "Derby": 26,
    "Leppävaara": 26,
    "Perkkaa": 27,
    "Redi": 27,
    "Tripla": 27,
    "Pasilan asema": 28,
    "Sture": 28,
    "Verkkosaari": 29,
    "Mäkelänkatu": 28,
    "Arabia": 26,
    "Arabianranta": 26,
    "Toukola": 26,
    "Naapuri": 26,
    "Kannelmäki": 25,
    "Maununneva": 25,
    "Pihlajisto": 24,
    "Siilitie": 24,
    "Latokartano": 23,
    "Myllypadontie": 24,
    "Kurkimäki": 26,
    "Mellunmäki": 26,
    "Rastila": 26,
    "Aurinkolahti": 27,
    "Roihuvuori": 27,
    "Herttoniemi": 27,
    "Sello": 28,
    "Lähderanta": 27,
    "Malmi": 28,
    "Malminmäki": 28,
    "Munkki": 28,
    "Merihaka": 29,
    "Kasarmi": 30,
    "Postitalo": 30,
    "Saari": 30,
    "Masurkka": 30,
    "Kasari": 30,
    "Iso Omena": 33,
    "Ruoholahti": 34,
    "Kivenlahti": 35,
    "Porvoo": 45,
    "Tarmola": 47,
    "Hyvinkäänkylä": 20,
    "Hyvinkää": 20,
    "Vieremä": 22,
    "Kumela": 48,
    "Riihimäki": 48,
    "Peltosaari": 48,
    "Munckinkatu": 48,
    "Hakalantori": 48,
    "Ukko-Pekka": 48,
    "Veturi": 48,
    "Turenki": 65,
    "Hämeensaari": 75,
    "Tiiriö": 78,
    "Hattula": 82,
    "Forssa": 120,
    "Orimattila": 60,
    "Laune": 68,
    "Paavola": 70,
    "Karisma": 72,
    "Okeroinen": 67,
    "Heinola": 105,
    "Kouvola": 135,
    "Kotka": 130,
    "Pasaati": 130,
    "Valkeakoski": 115,
    "Ideapark": 135,
    "Lielahti": 150,
    "Turtola": 145,
    "Linnainmaa": 145,
    "Pirkkala": 145,
    "Nokia": 150,
    "HerkkuDuo": 145,
    "Pirkanpoika": 140,
    "Löytis": 140,
    "Jämsä": 205,
}


def get_distance(store_name: str) -> float:
    s_lower = store_name.lower()
    for key, dist in TUUSULA_DISTANCES.items():
        if key.lower() in s_lower:
            return float(dist)

    if any(x in s_lower for x in ["tuusula", "hyrylä"]):
        return 1.0
    if any(x in s_lower for x in ["järvenpää"]):
        return 10.0
    if any(x in s_lower for x in ["kerava"]):
        return 12.0
    if any(x in s_lower for x in ["vantaa", "korso", "tikkurila", "koivukylä"]):
        return 18.0
    if any(x in s_lower for x in ["sipoo"]):
        return 25.0
    if any(x in s_lower for x in ["helsinki", "espoo", "kauniainen"]):
        return 28.0
    if any(x in s_lower for x in ["nurmijärvi", "rajamäki", "klaukkala"]):
        return 22.0
    if any(x in s_lower for x in ["hyvinkää"]):
        return 20.0
    if any(x in s_lower for x in ["mäntsälä", "porvoo"]):
        return 35.0
    if any(
        x in s_lower
        for x in ["riihimäki", "lohja", "vihti", "nummela", "kirkkonummi"]
    ):
        return 48.0
    if any(x in s_lower for x in ["lahti", "orimattila"]):
        return 65.0
    if any(x in s_lower for x in ["hämeenlinna", "turenki"]):
        return 75.0

    return 120.0


def set_store_to_hyrra(page):
    try:
        page.goto("https://www.k-ruoka.fi/kauppa/k-supermarket-hyrra", timeout=30000)
        page.wait_for_timeout(2000)
        onetrust_btn = page.locator(
            '#onetrust-accept-btn-handler, button:has-text("Hyväksy kaikki")'
        )
        if onetrust_btn.count() > 0:
            onetrust_btn.first.click(force=True, timeout=3000)
            page.wait_for_timeout(1000)
        select_btn = page.locator(
            'button:has-text("Valitse kaupaksi"), button:has-text("Valitse tämä kauppa")'
        )
        if select_btn.count() > 0 and select_btn.first.is_visible():
            select_btn.first.click(force=True, timeout=3000)
            page.wait_for_timeout(1000)
    except Exception:
        pass


def get_store_links_from_page(page):
    try:
        avail_btn = page.locator('button:has-text("Saatavuus muissa kaupoissa")')
        if avail_btn.count() == 0:
            avail_btn = page.locator('text="Saatavuus muissa kaupoissa"')

        if avail_btn.count() > 0:
            avail_btn.first.click(timeout=3000)
            page.wait_for_timeout(1000)
            for _ in range(6):
                more_btn = page.locator(
                    'button:has-text("Näytä lisää"), button:has-text("Lataa lisää")'
                )
                if more_btn.count() > 0 and more_btn.first.is_visible():
                    try:
                        more_btn.first.click(timeout=1000)
                    except Exception:
                        pass
                page.evaluate("window.scrollBy(0, 1000);")
                page.wait_for_timeout(400)
    except Exception:
        pass

    return page.evaluate("""
        () => {
            const results = [];
            const storeElements = document.querySelectorAll('[class*="StoreLink"], a[href*="/kauppa/kauppa/"]');
            storeElements.forEach(el => {
                const name = el.innerText ? el.innerText.trim().split('\\n')[0] : '';
                const href = el.getAttribute('href');
                if (name && href && !name.includes('Wolt') && !results.some(r => r.name === name)) {
                    const fullUrl = href.startsWith('http') ? href : 'https://www.k-ruoka.fi' + href;
                    results.push({ name, url: fullUrl });
                }
            });
            return results;
        }
    """)


def check_product_group(
    search_url: str,
    group_label: str,
    target_store_count: int = 50,
    required_keywords: list = None,
    exclude_keywords: list = None,
    liters: float = 7.92,
    total_deposit: float = 0.0,
):
    print(f"\n🥤 HAETAAN KATEGORIA: {group_label.upper()}")

    if required_keywords is None:
        required_keywords = []
    if exclude_keywords is None:
        exclude_keywords = []

    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=is_ci,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--start-maximized",
            ],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                " (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="fi-FI",
            viewport={"width": 1280, "height": 900},
            extra_http_headers={"Accept-Language": "fi-FI,fi;q=0.9"},
        )
        page = context.new_page()
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        set_store_to_hyrra(page)
        page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(1500)

        stores_to_visit = []
        visited_urls = set()

        initial_stores = get_store_links_from_page(page)
        print(f"Löytyi {len(initial_stores)} kauppaa kiertoon.")
        for s in initial_stores:
            if s["url"] not in visited_urls:
                stores_to_visit.append(s)

        master_store_data = []
        idx = 0

        while (
            idx < len(stores_to_visit)
            and len(master_store_data) < target_store_count
        ):
            current_store = stores_to_visit[idx]
            store_name = current_store["name"]
            store_url = current_store["url"]
            visited_urls.add(store_url)

            dist = get_distance(store_name)
            print(
                f"[{len(master_store_data)+1}/{target_store_count}] {store_name}"
                f" ({dist:.0f} km)",
                end=", ",
                flush=True,
            )

            try:
                page.goto(store_url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(1000)

                store_products = page.evaluate("""
                    () => {
                        const items = [];
                        const h1 = document.querySelector('h1');
                        const mainPriceEl = document.querySelector('[class*="price-container"], [class*="Price"], [class*="price"]');
                        if (h1) {
                            const name = h1.innerText.trim().replace(/\\n/g, ' ');
                            const price = mainPriceEl ? mainPriceEl.innerText.trim().replace(/\\n/g, ' ') : '';
                            items.push({ name, price });
                        }

                        const cards = document.querySelectorAll('article, [class*="productCard"], [class*="ProductCard"], a[href*="/kauppa/tuote/"]');
                        cards.forEach(card => {
                            const nameEl = card.querySelector('h3, h4, [class*="title"], [class*="Name"]');
                            const priceEl = card.querySelector('[class*="price"], [class*="Price"]');
                            if (nameEl) {
                                const name = nameEl.innerText.trim().replace(/\\n/g, ' ');
                                const price = priceEl ? priceEl.innerText.trim().replace(/\\n/g, ' ') : '';
                                if (name.length > 3 && !items.some(i => i.name === name)) {
                                    items.push({ name, price });
                                }
                            }
                        });
                        return items;
                    }
                """)

                print(f"Löytyi {len(store_products)} tuotetta.")
                master_store_data.append({
                    "store": store_name,
                    "distance": dist,
                    "products": store_products,
                })

                new_stores = get_store_links_from_page(page)
                for ns in new_stores:
                    if ns["url"] not in visited_urls and not any(
                        s["url"] == ns["url"] for s in stores_to_visit
                    ):
                        stores_to_visit.append(ns)
            except Exception as e:
                print(f"Virhe: {e}")

            idx += 1

        browser.close()

        for store_info in master_store_data:
            s_name = store_info["store"]
            s_dist = store_info["distance"]

            if store_info["products"]:
                for p in store_info["products"]:
                    p_name = p["name"].lower()

                    if required_keywords and not all(
                        req in p_name for req in required_keywords
                    ):
                        continue
                    if any(ex in p_name for ex in exclude_keywords):
                        continue

                    match = re.search(r"(\d+[\.,]\d+)\s*€", p["price"])
                    if match:
                        raw_val = float(match.group(1).replace(",", "."))
                        # Hinta pidetään kokonaisena (pohjahinta sisältää pantin), mutta pantti tallennetaan erikseen litrahintalaskentaa varten
                        results.append({
                            "store": s_name,
                            "distance": s_dist,
                            "product": p["name"],
                            "basePrice": raw_val,
                            "liters": liters,
                            "deposit": total_deposit,
                        })

    return results


def git_push_updates():
    print("\n🔄 Päivitetään data.json GitHub-repositorioosi...")
    try:
        subprocess.run(["git", "add", "data.json"], check=True)
        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                "Automated price update from local scraper [skip ci]",
            ],
            check=True,
        )
        subprocess.run(["git", "push"], check=True)
        print("🚀 Päivitys työnnetty GitHubiin!")
    except subprocess.CalledProcessError:
        print("ℹ️ Ei uusia muutoksia pushattavaksi tai git-komento epäonnistui.")


if __name__ == "__main__":
    res_limut = check_product_group(
        search_url=(
            "https://www.k-ruoka.fi/kauppa/tuotehaku?haku=Coca%20cola&tuote=coca-cola-zero-033l-kmp-24-pack-6415600550413"
        ),
        group_label="24-packit (Limut)",
        target_store_count=50,
        required_keywords=["24"],
        exclude_keywords=["novelle", "kivennäisvesi", "vichy"],
        liters=7.92,
        total_deposit=2.40,  # 24 * 0.10€
    )

    res_novelle = check_product_group(
        search_url=(
            "https://www.k-ruoka.fi/kauppa/tuotehaku?haku=novelle&tuote=novelle-kivennaisve-033l-kmp-24-pack-6413601003846"
        ),
        group_label="24-packit (Novelle Kivennäisvedet)",
        target_store_count=50,
        required_keywords=["novelle"],
        exclude_keywords=[],
        liters=7.92,
        total_deposit=2.40,  # 24 * 0.10€
    )

    res_18pack = check_product_group(
        search_url=(
            "https://www.k-ruoka.fi/kauppa/tuotehaku/juomat/virvoitusjuomat/cola-juomat?tuote=pepsi-max-033l-kmp-18-pack-6413605291584"
        ),
        group_label="18-packit",
        target_store_count=50,
        required_keywords=["18"],
        exclude_keywords=["novelle", "kivennäisvesi"],
        liters=5.94,
        total_deposit=1.80,  # 18 * 0.10€
    )

    res_18pack_tulkki = check_product_group(
        search_url=(
            "https://www.k-ruoka.fi/haku?q=24%20pack%20pepsi&tuote=pepsi-max-033l-tlk-18-pack-6413605203440"
        ),
        group_label="18-packit (Tölkki)",
        target_store_count=50,
        required_keywords=["18"],
        exclude_keywords=["novelle", "kivennäisvesi"],
        liters=5.94,
        total_deposit=2.70,  # 18 * 0.15€
    )

    res_6pack = check_product_group(
        search_url=(
            "https://www.k-ruoka.fi/kauppa/tuotehaku?haku=Pepsi%20max&tuote=pepsi-max-033l-tlk-6-pack-6413605015555"
        ),
        group_label="6-packit",
        target_store_count=50,
        required_keywords=["6"],
        exclude_keywords=["dippi", "taffel", "mauste", "kastike", "chip"],
        liters=1.98,
        total_deposit=0.90,  # 6 * 0.15€
    )

    res_muumilimu = check_product_group(
        search_url=(
            "https://www.k-ruoka.fi/kauppa/tuotehaku?haku=Muumi&tuote=muumi-metsamansikka-sokeriton-05l-kmp-6415600566667"
        ),
        group_label="Muumilimu",
        target_store_count=50,
        required_keywords=["0,5l"],
        exclude_keywords=["dippi", "taffel", "mauste", "kastike", "chip"],
        liters=0.5,
        total_deposit=0.20,
    )

    res_drpepper = check_product_group(
        search_url=(
            "https://www.k-ruoka.fi/kauppa/tuotehaku/juomat/virvoitusjuomat?tuote=dr-pepper-original-033l-tlk-6-pack-6415600596589"
        ),
        group_label="Dr. Pepper",
        target_store_count=50,
        required_keywords=["dr", "pepper"],  # Vaaditaan nimenomaan Dr. Pepper
        exclude_keywords=["dippi", "taffel", "mauste", "kastike", "chip"],
        liters=1.98,
        total_deposit=0.90,  # 6 * 0.15€
    )

    # Kerätään kaikki tuotteet kokonaisvertailuun
    res_kokonais = (
        res_limut
        + res_novelle
        + res_18pack
        + res_18pack_tulkki
        + res_6pack
        + res_muumilimu
        + res_drpepper
    )

    output_data = {
        "kokonaisvertailu": {
            "name": "🏆 Kaikki (Paras litrahinta)",
            "buyQuantity": 1,
            "items": res_kokonais,
        },
        "24-pack-limut": {
            "name": "24-packit (Limut)",
            "buyQuantity": 2,
            "items": res_limut,
        },
        "novelle": {
            "name": "24-packit (Novelle)",
            "buyQuantity": 2,
            "items": res_novelle,
        },
        "18-pack": {"name": "18-packit", "buyQuantity": 2, "items": res_18pack},
        "18-pack-tulkki": {
            "name": "18-packit (Tölkki)",
            "buyQuantity": 2,
            "items": res_18pack_tulkki,
        },
        "6-pack": {"name": "6-packit", "buyQuantity": 4, "items": res_6pack},
        "muumilimu": {
            "name": "Muumilimu (0.5L)",
            "buyQuantity": 4,
            "items": res_muumilimu,
        },
        "dr-pepper": {"name": "Dr. Pepper", "buyQuantity": 4, "items": res_drpepper},
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)

    print("\n✅ Kaikki tiedot tallennettu onnistuneesti tiedostoon data.json!")
    git_push_updates()