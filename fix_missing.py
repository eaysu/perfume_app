"""
1. Scrape Afnan brand (15 perfumes) - missing from JSON
2. Re-scrape 4 perfumes with incomplete vote data
3. Fix Dolce&Gabbana / Jo Malone image_local filename encoding (&amp; -> &)
"""
import json, os, re, time, random
from selenium_scraper import SeleniumPerfumeScraper

JSON_FILE  = "fragrantica_perfumes.json"
IMAGE_DIR  = "perfume_images"
VOTE_FIELDS = ['longevity', 'sillage', 'price_value', 'season', 'main_accords']

# Perfumes with incomplete vote data (URL -> missing fields)
INCOMPLETE = [
    "https://www.fragrantica.com/perfume/Lancome/Idole-55795.html",
    "https://www.fragrantica.com/perfume/Essential-Parfums/Bois-Imperial-Hair-Body-Mist-112864.html",
    "https://www.fragrantica.com/perfume/Amouage/Lilac-Love-35624.html",
    "https://www.fragrantica.com/perfume/Maison-Alhambra/Sceptre-Malachite-94163.html",
]


def sanitize_filename(name):
    name = re.sub(r'[<>:"/\\|?*&]', '', name)
    name = re.sub(r'\s+', '_', name.strip())
    return name[:80]


def fix_image_encodings(data):
    """Fix image_local paths that contain &amp; instead of plain &"""
    fixed = 0
    for p in data:
        local = p.get("image_local", "")
        if "&amp;" in local:
            corrected = local.replace("&amp;", "")
            # Check if correct file actually exists
            if os.path.exists(corrected):
                p["image_local"] = corrected
                fixed += 1
            else:
                # Try without & entirely (sanitize_filename strips &)
                p["image_local"] = corrected
                fixed += 1
    print(f"  Fixed {fixed} image_local encoding issues")
    return data


def main():
    with open(JSON_FILE, encoding="utf-8") as f:
        data = json.load(f)

    print(f"Loaded {len(data)} perfumes from JSON\n")

    scraper = SeleniumPerfumeScraper(headless=False)

    try:
        # ── 1. Fix image_local encodings ─────────────────────────────
        print("=" * 60)
        print("STEP 1: Fix image_local encoding issues")
        print("=" * 60)
        data = fix_image_encodings(data)

        # ── 2. Scrape Afnan brand ─────────────────────────────────────
        print("\n" + "=" * 60)
        print("STEP 2: Scrape Afnan brand")
        print("=" * 60)
        afnan_exists = any(p.get("brand", "").lower() == "afnan" for p in data)
        if afnan_exists:
            print("  Afnan already in JSON, skipping scrape")
        else:
            afnan_perfumes = scraper.scrape_brand("Afnan", 15)
            if afnan_perfumes:
                for p in afnan_perfumes:
                    p["category"] = "designer"
                    # Download image
                    img_url = p.get("image_url", "")
                    name    = p.get("name", "")
                    brand   = p.get("brand", "Afnan")
                    if img_url and name:
                        fname = sanitize_filename(f"{brand}_{name}") + ".png"
                        fpath = os.path.join(IMAGE_DIR, fname)
                        os.makedirs(IMAGE_DIR, exist_ok=True)
                        if not os.path.exists(fpath):
                            scraper.download_image(img_url, fpath)
                        if os.path.exists(fpath):
                            p["image_local"] = fpath
                data.extend(afnan_perfumes)
                print(f"  Added {len(afnan_perfumes)} Afnan perfumes")
            else:
                print("  WARNING: Afnan scrape returned 0 results")
            time.sleep(random.uniform(2, 4))

        # ── 3. Re-scrape incomplete vote data ─────────────────────────
        print("\n" + "=" * 60)
        print("STEP 3: Re-scrape incomplete vote fields")
        print("=" * 60)

        url_to_idx = {p.get("url", ""): i for i, p in enumerate(data)}

        for url in INCOMPLETE:
            idx = url_to_idx.get(url)
            if idx is None:
                print(f"  [NOT FOUND IN JSON] {url}")
                continue

            p = data[idx]
            missing = [f for f in VOTE_FIELDS if not p.get(f)]
            print(f"\n  {p.get('brand')} — {p.get('name')}")
            print(f"  Missing: {missing}")

            try:
                fresh = scraper.extract_perfume_details(url)
                if not fresh:
                    print(f"  WARN: No data returned")
                    continue
                updated = 0
                for field in missing:
                    val = fresh.get(field)
                    if val:
                        data[idx][field] = val
                        updated += 1
                        print(f"    ✓ {field}: {val}")
                    else:
                        print(f"    ✗ {field}: still missing")
                print(f"  Updated {updated}/{len(missing)} fields")
            except Exception as e:
                print(f"  ERROR: {e}")

            time.sleep(random.uniform(3, 6))

        # ── 4. Save ───────────────────────────────────────────────────
        print("\n" + "=" * 60)
        print("STEP 4: Save updated JSON")
        print("=" * 60)
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  Saved {len(data)} perfumes to {JSON_FILE}")

    finally:
        scraper.close()
        print("\nDone.")


if __name__ == "__main__":
    main()
