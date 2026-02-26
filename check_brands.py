"""
Compare target brand list vs JSON, show per-brand perfume counts,
and list the 4 perfumes with missing vote fields.
"""
import json
from collections import defaultdict

TARGET_BRANDS = [
    # Designer
    "Dior", "Yves Saint Laurent", "Gucci", "Chanel", "Giorgio Armani",
    "Versace", "Tom Ford", "Burberry", "Givenchy", "Lancome",
    "Dolce & Gabbana", "Paco Rabanne", "Hugo Boss", "Prada",
    "Narciso Rodriguez", "Jo Malone London", "Guerlain", "Kenzo",
    "Chloé", "Elie Saab", "Ferragamo", "Cacharel", "Jean Paul Gaultier",
    "Calvin Klein", "Police", "Trussardi", "Montblanc",
    "Maison Martin Margiela",
    # Niche
    "Hermès", "Acqua di Parma", "Creed", "Byredo", "Kilian", "Xerjoff",
    "Sospiro", "Ex Nihilo", "The Merchant Of Venice", "Parfums de Marly",
    "Memo Paris", "Initio", "Penhaligons", "Tiziana Terenzi",
    "Maison Crivelli", "Maison Francis Kurkdjian", "Atkinsons", "Mancera",
    "Essential Parfums", "Toskovat", "Nishane",
    # Added later
    "Lattafa Perfumes", "Armaf", "Amouage", "Zara", "French Avenue",
    "Maison Alhambra", "PARIS CORNER", "Louis Vuitton", "Afnan",
    "Carolina Herrera", "Valentino", "Diptyque", "Bath & Body Works",
]

VOTE_FIELDS = ['longevity', 'sillage', 'price_value', 'season', 'main_accords']

with open("fragrantica_perfumes.json", encoding="utf-8") as f:
    data = json.load(f)

# Count per brand in JSON (case-insensitive match)
brand_counts = defaultdict(int)
brand_actual = {}  # canonical name -> actual name in JSON
for p in data:
    b = p.get("brand", "")
    brand_counts[b.lower()] += 1
    brand_actual[b.lower()] = b

print("=" * 65)
print("  BRAND COVERAGE")
print("=" * 65)
print(f"  {'Brand':<32} {'In JSON':>8}  {'Status'}")
print(f"  {'-'*32}  {'-'*8}  {'-'*10}")

missing_brands = []
for brand in sorted(TARGET_BRANDS, key=str.lower):
    key = brand.lower()
    count = brand_counts.get(key, 0)
    # fuzzy: try substring match if exact fails
    if count == 0:
        for k, v in brand_counts.items():
            if brand.lower() in k or k in brand.lower():
                count = v
                break
    status = "✅" if count > 0 else "❌ MISSING"
    if count == 0:
        missing_brands.append(brand)
    print(f"  {brand:<32} {count:>8}  {status}")

print()
print(f"  Target brands : {len(TARGET_BRANDS)}")
print(f"  Found in JSON : {len(TARGET_BRANDS) - len(missing_brands)}")
print(f"  Missing       : {len(missing_brands)}")
if missing_brands:
    print(f"\n  Missing brands: {missing_brands}")

# Per-brand total
print()
print("=" * 65)
print("  ALL BRANDS IN JSON (sorted by count)")
print("=" * 65)
for b, cnt in sorted(brand_counts.items(), key=lambda x: -x[1]):
    print(f"  {brand_actual[b]:<35} {cnt:>4} perfumes")

# Missing vote fields detail
print()
print("=" * 65)
print("  PERFUMES WITH INCOMPLETE VOTE DATA")
print("=" * 65)
for p in data:
    missing = [f for f in VOTE_FIELDS if not p.get(f)]
    if missing:
        print(f"  {p.get('brand')} — {p.get('name')}")
        print(f"    URL: {p.get('url','')}")
        print(f"    Missing: {', '.join(missing)}")
        print()
