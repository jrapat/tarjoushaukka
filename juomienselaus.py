import json
import os
import re
import subprocess
from playwright.sync_api import sync_playwright

# Tarkistetaan automaattisesti, ajetaanko skriptiä GitHub Actionsissa (CI) vai omalla koneella
is_ci = os.getenv("CI") is not None

# Kattava etäisyyssanakirja Tuusulasta (km yhdensuuntaisesti)
TUUSULA_DISTANCES = {
    "Hyrrä": 1,
    "Lahela": 3,
    "Hyrylä": 1,
    "Parila": 5,
    "Järvenpää": 10,
    "Pajala": 11,
    "Kerava": 12,
    "Karuselli": 12,
    "Kellokoski": 14,
    "Kivistö": 14,
    "Koivukylä": 17,
    "Tammisto": 18,
    "Jumbo": 18,
    "Hyvinkää": 20,
    "Manteli": 20,
    "Martsari": 21,
    "Myyrmäki": 22,
    "Niipperi": 22,
    "Klaukkala": 22,
    "Pähkinärinne": 25,
    "Konala": 25,
    "Sello": 28,
    "Malmi": 28,
    "Malminmäki": 28,
    "Arabia": 18,
    "Hakunila": 15,
    "Honkatori": 22,
    "Masi": 20,
    "Easton": 25,
    "Columbus": 25,
    "Mäntsälä": 32,
    "Kivenlahti": 35,
    "Ruoholahti": 34,
    "Porvoo": 45,
    "Riihimäki": 48,
    "Lohja": 45,
    "Nummela": 45,
    "Kirkkonummi": 48,
    "Hämeensaari": 75,
    "Forssa": 120,
    "Kouvola": 150,
    "Lielahti": 150,
    "Jämsä": 205,
}


def get_distance(store_name: str) -> float:
  s_lower = store_name.lower()
  for key, dist in TUUSULA_DISTANCES.items():
    if key.lower() in s_lower:
      return float(dist)

  if any(
      x in s_lower
      for x in [
          "tuusula",
          "järvenpää",
          "kerava",
          "vantaa",
          "helsinki",
          "espoo",
          "nurmijärvi",
          "sipoo",
      ]
  ):
    return 20.0
  if any(
      x in s_lower
      for x in ["hyvinkää", "mäntsälä", "porvoo", "lohja", "vihti", "riihimäki"]
  ):
    return 45.0
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
        'button:has-text("Valitse kaupaksi"), button:has-text("Valitse tämä'
        ' kauppa")'
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
        idx < len(stores_to_visit) and len(master_store_data) < target_store_count
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
            val = float(match.group(1).replace(",", "."))
            results.append({
                "store": s_name,
                "distance": s_dist,
                "product": p["name"],
                "basePrice": val,
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
  )

  res_novelle = check_product_group(
      search_url=(
          "https://www.k-ruoka.fi/kauppa/tuotehaku?haku=novelle&tuote=novelle-kivennaisve-033l-kmp-24-pack-6413601003846"
      ),
      group_label="24-packit (Novelle Kivennäisvedet)",
      target_store_count=50,
      required_keywords=["novelle"],
      exclude_keywords=[],
  )

  res_18pack = check_product_group(
      search_url=(
          "https://www.k-ruoka.fi/kauppa/tuotehaku/juomat/virvoitusjuomat/cola-juomat?tuote=pepsi-max-033l-kmp-18-pack-6413605291584"
      ),
      group_label="18-packit",
      target_store_count=50,
      required_keywords=["18"],
      exclude_keywords=["novelle", "kivennäisvesi"],
  )

  res_6pack = check_product_group(
      search_url=(
          "https://www.k-ruoka.fi/kauppa/tuotehaku?haku=Pepsi%20max&tuote=pepsi-max-033l-tlk-6-pack-6413605015555"
      ),
      group_label="6-packit",
      target_store_count=50,
      required_keywords=["6"],
      exclude_keywords=["dippi", "taffel", "mauste", "kastike", "chip"],
  )

  output_data = {
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
      "6-pack": {"name": "6-packit", "buyQuantity": 4, "items": res_6pack},
  }

  with open("data.json", "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False, indent=4)

  print("\n✅ Kaikki tiedot tallennettu onnistuneesti tiedostoon data.json!")

  # Ajetaan git push automaattisesti haun jälkeen
  git_push_updates()
  