"""
500 karakterde kesilmiş description'ları tespit et ve yeniden çek.
"""
import json
import time
import random
from selenium_scraper import SeleniumPerfumeScraper

INPUT_FILE = "fragrantica_perfumes.json"

with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    perfumes = json.load(f)

# ~500 karakterde kesilmiş olanları bul
truncated = [
    p for p in perfumes
    if p.get('description') and 490 <= len(p['description']) <= 510
]

print(f"📦 Toplam parfüm: {len(perfumes)}")
print(f"✂️  500 char'da kesilmiş description: {len(truncated)}")
for p in truncated[:10]:
    print(f"   • {p.get('brand')} - {p.get('name')}: {len(p['description'])} chars")
if len(truncated) > 10:
    print(f"   ... ve {len(truncated)-10} tane daha")

if not truncated:
    print("✅ Kesilmiş description yok!")
    exit()

print(f"\n🔄 {len(truncated)} parfüm yeniden çekilecek...\n")

scraper = SeleniumPerfumeScraper(headless=False)
updated = 0
failed = 0

try:
    for i, p in enumerate(truncated, 1):
        url = p.get('url', '')
        if not url:
            continue
        print(f"[{i}/{len(truncated)}] {p.get('brand')} - {p.get('name')}")
        try:
            result = scraper.extract_perfume_details(url)
        except Exception as e:
            print(f"  ❌ Hata: {e}")
            failed += 1
            time.sleep(random.uniform(8, 12))
            continue
        if result and result.get('description') and len(result['description']) > len(p.get('description', '')):
            for main_p in perfumes:
                if main_p.get('url') == url:
                    old_len = len(main_p.get('description', ''))
                    main_p['description'] = result['description']
                    print(f"  ✅ {old_len} → {len(result['description'])} chars")
                    updated += 1
                    break
        else:
            print(f"  ⚠️  No improvement")
            failed += 1
        # Save every 5
        if i % 5 == 0:
            with open(INPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(perfumes, f, ensure_ascii=False, indent=2)
            print(f"  💾 Kaydedildi ({updated} güncellendi)")
        time.sleep(random.uniform(4, 7))
except KeyboardInterrupt:
    print("\n⚠️  Durduruldu")
finally:
    scraper.close()

with open(INPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(perfumes, f, ensure_ascii=False, indent=2)

print(f"\n✅ Güncellendi: {updated} | ⚠️ Değişmedi: {failed}")
print(f"💾 Kaydedildi: {len(perfumes)} parfüm")
