"""
Eksik/hatalı veri raporu - manuel düzeltme için.
Çıktıyı missing_report.txt'e kaydeder.
"""
import json, os, re

JSON_FILE = "fragrantica_perfumes.json"
IMG_DIR   = "perfume_images"
VOTE_FIELDS = ['longevity', 'sillage', 'price_value', 'main_accords', 'season']
NOTE_FIELDS = ['top_notes', 'middle_notes', 'base_notes']
URL_PATTERN = re.compile(r"https?://www\.fragrantica\.com/perfume/")

with open(JSON_FILE, encoding="utf-8") as f:
    data = json.load(f)

lines = []
lines.append(f"TOPLAM PARFÜM: {len(data)}")
lines.append("=" * 70)

issues_found = 0

for p in data:
    name  = p.get("name", "?")
    brand = p.get("brand", "?")
    url   = p.get("url", "")
    label = f"{brand} — {name}"
    problems = []

    # 1. image_local eksik veya dosya yok
    local = p.get("image_local", "")
    if not local:
        problems.append("image_local: YOK (alan boş)")
    elif not os.path.exists(local):
        problems.append(f"image_local: DOSYA YOK → {local}")

    # 2. image_url eksik
    if not p.get("image_url"):
        problems.append("image_url: YOK")

    # 3. Notes eksik
    if not any(p.get(f) for f in NOTE_FIELDS):
        problems.append("notes: top/middle/base hepsi boş")

    # 4. Vote field'ları eksik
    for vf in VOTE_FIELDS:
        val = p.get(vf)
        if val is None or val == {} or val == []:
            problems.append(f"{vf}: EKSİK")

    # 5. URL eksik veya hatalı format
    if not url:
        problems.append("url: YOK")
    elif not URL_PATTERN.match(url):
        problems.append(f"url: HATALI FORMAT → {url}")

    # 6. Description eksik veya çok kısa
    desc = p.get("description", "")
    if not desc:
        problems.append("description: YOK")
    elif len(desc) < 80:
        problems.append(f"description: ÇOK KISA ({len(desc)} karakter)")

    if problems:
        issues_found += 1
        lines.append(f"\n[{issues_found}] {label}")
        lines.append(f"    URL: {url}")
        for prob in problems:
            lines.append(f"    ✗ {prob}")

lines.append("\n" + "=" * 70)
lines.append(f"TOPLAM SORUNLU PARFÜM: {issues_found} / {len(data)}")

output = "\n".join(lines)
print(output)

with open("missing_report.txt", "w", encoding="utf-8") as f:
    f.write(output)
print(f"\n→ missing_report.txt dosyasına kaydedildi.")
