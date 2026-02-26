"""Update existing JSON with longevity, sillage, price_value, season vote data.
Also scrapes new brands (Nishane) if not already in JSON.
"""
import json
import os
import re
import time
import random
from selenium_scraper import SeleniumPerfumeScraper

JSON_FILE = 'fragrantica_perfumes.json'
VOTE_FIELDS = ['longevity', 'sillage', 'price_value', 'season', 'main_accords']
NEW_BRANDS = {
    'Lattafa Perfumes': 'designer',
    'Armaf': 'designer',
    'Amouage': 'niche',
    'Zara': 'designer',
    'French Avenue': 'designer',
    'Maison Alhambra': 'designer',
    'PARIS CORNER': 'designer',
    'Louis Vuitton': 'luxury',
    'Afnan': 'designer',
    'Carolina Herrera': 'designer',
    'Valentino': 'designer',
    'Diptyque': 'niche',
    'Bath & Body Works': 'designer',
}
PERFUMES_PER_BRAND = 15
IMAGE_DIR = 'perfume_images'
NOTES_DIR = 'perfume_notes'

def sanitize_filename(name):
    name = re.sub(r'[<>:"/\\|?*&]', '', name)
    name = re.sub(r'\s+', '_', name.strip())
    return name[:80]

def needs_update(perfume):
    return not all(perfume.get(f) for f in VOTE_FIELDS)

def main():
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    existing_brands = {p.get('brand') for p in data}
    brands_to_scrape = {b: c for b, c in NEW_BRANDS.items() if b not in existing_brands}

    to_update = [p for p in data if needs_update(p)]
    print(f"Total parfums: {len(data)}")
    print(f"Needs vote update: {len(to_update)}")
    print(f"New brands to scrape: {list(brands_to_scrape.keys()) or 'none'}")

    scraper = SeleniumPerfumeScraper(headless=False)

    # --- Scrape new brands first ---
    if brands_to_scrape:
        os.makedirs(IMAGE_DIR, exist_ok=True)
        for brand_name, category in brands_to_scrape.items():
            print(f"\n🆕 Scraping new brand: {brand_name}")
            try:
                brand_perfumes = scraper.scrape_brand(brand_name, PERFUMES_PER_BRAND)
                if brand_perfumes:
                    for p in brand_perfumes:
                        p['category'] = category
                        # Download image
                        img_url = p.get('image_url')
                        if img_url and p.get('name'):
                            fname = sanitize_filename(f"{brand_name}_{p['name']}") + ".png"
                            fpath = os.path.join(IMAGE_DIR, fname)
                            if not os.path.exists(fpath):
                                scraper.download_image(img_url, fpath)
                            p['image_local'] = fpath
                    data.extend(brand_perfumes)
                    to_update.extend(brand_perfumes)
                    print(f"  ✅ Added {len(brand_perfumes)} perfumes from {brand_name}")
                else:
                    print(f"  ❌ No perfumes found for {brand_name}")
            except Exception as e:
                print(f"  ❌ Error scraping {brand_name}: {e}")
            time.sleep(random.uniform(3, 5))

        # Save after new brands
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Saved {len(data)} perfumes after new brand scraping")

    if not to_update:
        print("Nothing to vote-update.")
        scraper.close()
        return

    os.makedirs(NOTES_DIR, exist_ok=True)
    updated = 0
    failed = 0

    def download_note_images(note_images_dict):
        """Download note images to NOTES_DIR, skip already existing."""
        for note_name, img_url in note_images_dict.items():
            fname = sanitize_filename(note_name) + '.png'
            fpath = os.path.join(NOTES_DIR, fname)
            if not os.path.exists(fpath) and img_url:
                scraper.download_image(img_url, fpath)

    try:
        for i, perfume in enumerate(to_update):
            url = perfume.get('url')
            name = perfume.get('name', '?')
            brand = perfume.get('brand', '?')
            print(f"\n[{i+1}/{len(to_update)}] {name} - {brand}")

            try:
                result = scraper.extract_perfume_details(url)
                if result:
                    changed = False
                    for field in VOTE_FIELDS:
                        val = result.get(field)
                        if val:
                            perfume[field] = val
                            changed = True
                    # Download note images (always, independent of vote fields)
                    note_imgs = result.get('note_images', {})
                    if note_imgs:
                        download_note_images(note_imgs)
                    if changed:
                        updated += 1
                        print(f"  ✅ Updated: {[f for f in VOTE_FIELDS if perfume.get(f)]}")
                    else:
                        failed += 1
                        print(f"  ⚠️  No vote data found")
                else:
                    failed += 1
                    print(f"  ❌ Scrape failed")
            except Exception as e:
                failed += 1
                print(f"  ❌ Error: {e}")

            # Save progress every 10 perfumes
            if (i + 1) % 10 == 0:
                with open(JSON_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"\n💾 Saved progress ({updated} updated, {failed} failed)")

            # Cooldown between requests
            time.sleep(random.uniform(2.5, 4.5))

    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    finally:
        scraper.close()
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Done. Updated: {updated}, Failed: {failed}")
        print(f"💾 Saved to {JSON_FILE}")

if __name__ == '__main__':
    main()
