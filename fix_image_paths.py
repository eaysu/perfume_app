"""
Fix image_local paths where the file on disk has no brand-suffix
but the JSON path has _BrandName appended before the extension.

Pattern:
  JSON says:  perfume_images/DolceGabbana_Light_Blue_Dolce&Gabbana.png
  Disk has:   perfume_images/DolceGabbana_Light_Blue.png

Strategy: for each missing image_local, try stripping the last
underscore-segment (the brand name) and also strip & chars.
"""
import json, os, re

JSON_FILE = "fragrantica_perfumes.json"
IMG_DIR   = "perfume_images"

with open(JSON_FILE, encoding="utf-8") as f:
    data = json.load(f)

fixed = 0
still_missing = []

for p in data:
    local = p.get("image_local", "")
    if local and os.path.exists(local):
        continue  # already fine

    if not local:
        continue  # no path at all, skip

    dirname  = os.path.dirname(local)
    basename = os.path.basename(local)          # e.g. DolceGabbana_Light_Blue_Dolce&Gabbana.png
    stem, ext = os.path.splitext(basename)      # stem, .png

    # Try candidates in order:
    candidates = []

    def strip_amp(s):
        return re.sub(r'_?&_?', '_', s).replace("__", "_").strip("_")

    # 1. Strip last _Segment(s) (brand suffix) — with and without &
    parts = stem.split("_")
    for drop in range(1, min(5, len(parts))):
        base = "_".join(parts[:-drop])
        candidates.append(base + ext)
        candidates.append(strip_amp(base) + ext)

    # 2. Also try stripping & from the original name (no suffix drop)
    candidates.append(strip_amp(stem) + ext)

    found = None
    for c in candidates:
        trial = os.path.join(dirname or IMG_DIR, c)
        if os.path.exists(trial):
            found = trial
            break

    if found:
        p["image_local"] = found
        fixed += 1
        print(f"  ✓ {p.get('brand')} — {p.get('name')}")
        print(f"      {local}")
        print(f"    → {found}")
    else:
        still_missing.append((p.get("brand"), p.get("name"), local))

print(f"\nFixed: {fixed}")
if still_missing:
    print(f"Still missing ({len(still_missing)}):")
    for brand, name, path in still_missing:
        print(f"  ✗ {brand} — {name}  →  {path}")

with open(JSON_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"\nSaved {len(data)} perfumes to {JSON_FILE}")
