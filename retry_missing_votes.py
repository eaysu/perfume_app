"""Re-scrape the 4 perfumes with missing vote fields using the fixed extractor."""
import json, time, random
from selenium_scraper import SeleniumPerfumeScraper

JSON_FILE = "fragrantica_perfumes.json"
VOTE_FIELDS = ['longevity', 'sillage', 'price_value', 'season', 'main_accords']

TARGETS = [
    "https://www.fragrantica.com/perfume/Lancome/Idole-55795.html",
    "https://www.fragrantica.com/perfume/Essential-Parfums/Bois-Imperial-Hair-Body-Mist-112864.html",
    "https://www.fragrantica.com/perfume/Amouage/Lilac-Love-35624.html",
    "https://www.fragrantica.com/perfume/Maison-Alhambra/Sceptre-Malachite-94163.html",
]

with open(JSON_FILE, encoding="utf-8") as f:
    data = json.load(f)

url_to_idx = {p.get("url", ""): i for i, p in enumerate(data)}

scraper = SeleniumPerfumeScraper(headless=False)

try:
    for url in TARGETS:
        idx = url_to_idx.get(url)
        if idx is None:
            print(f"[NOT FOUND] {url}")
            continue
        p = data[idx]
        missing = [f for f in VOTE_FIELDS if not p.get(f)]
        print(f"\n{'='*60}")
        print(f"{p.get('brand')} — {p.get('name')}")
        print(f"Missing: {missing}")

        fresh = scraper.extract_perfume_details(url)
        if not fresh:
            print("  ERROR: No data returned")
            continue

        updated = 0
        for field in VOTE_FIELDS:
            val = fresh.get(field)
            old = p.get(field)
            if val and not old:
                data[idx][field] = val
                updated += 1
                print(f"  ✓ {field}: {val}")
            elif val and old:
                print(f"  = {field}: already set")
            else:
                print(f"  ✗ {field}: still missing")

        print(f"  → Updated {updated} new fields")
        time.sleep(random.uniform(3, 5))

    print(f"\n{'='*60}")
    print("Saving JSON...")
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(data)} perfumes.")

finally:
    scraper.close()
