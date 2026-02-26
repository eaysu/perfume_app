"""
Scrape top 15 most popular perfumes from Designer and Niche brands
Output: fragrantica_perfumes.json + perfume_images/ folder
"""

from selenium_scraper import SeleniumPerfumeScraper
import json
import os
import re
import time
from tqdm import tqdm


def sanitize_filename(name: str) -> str:
    """Convert perfume name to a safe filename"""
    name = re.sub(r'[<>:"/\\|?*&]', '', name)
    name = re.sub(r'\s+', '_', name.strip())
    return name[:80]


def download_all_images(scraper, perfumes, image_dir="perfume_images"):
    """Download all perfume images to a folder as .png"""
    os.makedirs(image_dir, exist_ok=True)
    
    downloaded = 0
    skipped = 0
    
    print(f"\n🖼️  Downloading {len(perfumes)} perfume images...")
    
    for p in tqdm(perfumes, desc="Downloading images", unit="img"):
        image_url = p.get('image_url')
        name = p.get('name')
        brand = p.get('brand')
        
        if not image_url or not name:
            skipped += 1
            continue
        
        filename = sanitize_filename(f"{brand}_{name}") + ".png"
        filepath = os.path.join(image_dir, filename)
        
        # Skip if already downloaded
        if os.path.exists(filepath):
            p['image_local'] = filepath
            downloaded += 1
            continue
        
        if scraper.download_image(image_url, filepath):
            p['image_local'] = filepath
            downloaded += 1
        else:
            skipped += 1
    
    print(f"✅ Downloaded: {downloaded} | ⚠️ Skipped: {skipped}")
    return downloaded


def main():
    # Designer Brands
    designer_brands = [
        "Dior",
        "Yves Saint Laurent",
        "Gucci",
        "Chanel",
        "Giorgio Armani",
        "Versace",
        "Tom Ford",
        "Burberry",
        "Givenchy",
        "Lancome",
        "Dolce & Gabbana",
        "Paco Rabanne",
        "Hugo Boss",
        "Prada",
        "Narciso Rodriguez",
        "Jo Malone London",
        "Guerlain",
        "Kenzo",
        "Chloé",
        "Elie Saab",
        "Ferragamo",
        "Cacharel",
        "Jean Paul Gaultier",
        "Calvin Klein",
        "Police",
        "Trussardi",
        "Montblanc",
    ]
    
    # Niche Brands
    niche_brands = [
        "Hermès",
        "Acqua di Parma",
        "Creed",
        "Byredo",
        "Kilian",
        "Xerjoff",
        "Sospiro",
        "Ex Nihilo",
        "The Merchant Of Venice",
        "Parfums de Marly",
        "Memo Paris",
        "Initio",
        "Penhaligons",
        "Tiziana Terenzi",
        "Maison Crivelli",
        "Maison Francis Kurkdjian",
        "Atkinsons",
        "Mancera",
        "Essential Parfums",
        "Toskovat",
        "Nishane",
    ]
    
    # Maison Martin Margiela is designer but has Replica sub-brand on Fragrantica
    designer_brands.append("Maison Martin Margiela")
    all_brands = designer_brands + niche_brands
    perfumes_per_brand = 15
    
    print("🚀 FRAGRANTICA PERFUME SCRAPER")
    print("=" * 60)
    print(f"📋 Designer Brands: {len(designer_brands)}")
    print(f"💎 Niche Brands: {len(niche_brands)}")
    print(f"📋 Total: {len(all_brands)} brands")
    print(f"🎯 Per brand: {perfumes_per_brand} perfumes")
    print(f"📊 Target: ~{len(all_brands) * perfumes_per_brand} perfumes")
    print("=" * 60)
    
    scraper = SeleniumPerfumeScraper(headless=True)
    
    all_perfumes = []
    successful_brands = []
    failed_brands = []
    
    try:
        # Brand progress bar
        brand_pbar = tqdm(all_brands, desc="Brands", unit="brand", position=0)
        
        for brand_name in brand_pbar:
            brand_pbar.set_postfix_str(brand_name)
            
            try:
                brand_perfumes = scraper.scrape_brand(brand_name, perfumes_per_brand)
                
                if brand_perfumes:
                    category = "designer" if brand_name in designer_brands else "niche"
                    for p in brand_perfumes:
                        p['category'] = category
                    
                    all_perfumes.extend(brand_perfumes)
                    successful_brands.append(brand_name)
                else:
                    failed_brands.append(brand_name)
                
                brand_pbar.set_description(f"Brands ({len(all_perfumes)} perfumes)")
                
                # Intermediate save every 5 brands
                idx = all_brands.index(brand_name) + 1
                if idx % 5 == 0 and all_perfumes:
                    with open("fragrantica_perfumes_partial.json", 'w', encoding='utf-8') as f:
                        json.dump(all_perfumes, f, ensure_ascii=False, indent=2)
                
            except Exception as e:
                failed_brands.append(brand_name)
                tqdm.write(f"❌ {brand_name} error: {str(e)[:150]}")
        
        brand_pbar.close()
        
        # === DOWNLOAD IMAGES ===
        download_all_images(scraper, all_perfumes)
        
        # === SUMMARY ===
        print("\n" + "=" * 60)
        print("📊 FINAL SUMMARY")
        print("=" * 60)
        print(f"✅ Successful Brands: {len(successful_brands)}/{len(all_brands)}")
        print(f"❌ Failed Brands: {len(failed_brands)}/{len(all_brands)}")
        print(f"📦 Total Perfumes: {len(all_perfumes)}")
        
        if failed_brands:
            print(f"\n⚠️ Failed Brands:")
            for brand in failed_brands:
                print(f"  - {brand}")
        
        # Category stats
        designer_perfumes = [p for p in all_perfumes if p.get('category') == 'designer']
        niche_perfumes = [p for p in all_perfumes if p.get('category') == 'niche']
        
        print(f"\n📊 Category Distribution:")
        print(f"  - Designer: {len(designer_perfumes)} perfumes")
        print(f"  - Niche: {len(niche_perfumes)} perfumes")
        
        # Completeness stats
        complete = [p for p in all_perfumes if p.get('name') and p.get('description') and 
                    (p.get('top_notes') or p.get('middle_notes') or p.get('base_notes'))]
        print(f"\n📊 Data Completeness: {len(complete)}/{len(all_perfumes)} ({100*len(complete)/max(len(all_perfumes),1):.1f}%)")
        
        # Top rated
        rated = [p for p in all_perfumes if p.get('rating')]
        if rated:
            top_rated = sorted(rated, key=lambda x: x.get('rating', 0), reverse=True)[:10]
            print("\n🏆 Top 10 Rated Perfumes:")
            for j, p in enumerate(top_rated, 1):
                print(f"  {j}. {p.get('name', 'N/A')} ({p.get('brand')}) - {p.get('rating')}/5")
        
        # Save final JSON (includes image_local paths)
        if all_perfumes:
            filename = "fragrantica_perfumes.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(all_perfumes, f, ensure_ascii=False, indent=2)
            print(f"\n💾 {len(all_perfumes)} perfumes saved to '{filename}'")
        
        # Cleanup partial file
        if os.path.exists("fragrantica_perfumes_partial.json"):
            os.remove("fragrantica_perfumes_partial.json")
        
        print("\n✅ Scraping completed!")
        
    finally:
        scraper.close()
        print("🔒 Browser closed")


if __name__ == "__main__":
    main()
