"""
Audit fragrantica_perfumes.json for completeness.
Checks: images, notes, longevity, sillage, price_value, main_accords, season, URLs.
"""
import json, os, re
from collections import defaultdict

JSON_PATH  = "fragrantica_perfumes.json"
IMG_DIR    = "perfume_images"
NOTE_IMG_DIR = "note_images"

with open(JSON_PATH, encoding="utf-8") as f:
    data = json.load(f)

perfumes = data if isinstance(data, list) else data.get("perfumes", [])
total = len(perfumes)
print(f"Total perfumes: {total}\n")

issues = defaultdict(list)  # category -> list of (brand, name)

vote_fields = ["longevity", "sillage", "price_value", "main_accords", "season"]
note_fields = ["top_notes", "middle_notes", "base_notes"]

missing_image_file   = []
missing_image_url    = []
missing_notes        = []
missing_vote_data    = defaultdict(list)
missing_url          = []
bad_url              = []
short_description    = []
no_description       = []
missing_any_vote     = []

url_pattern = re.compile(r"https?://www\.fragrantica\.com/perfume/")

for p in perfumes:
    name  = p.get("name", "?")
    brand = p.get("brand", "?")
    label = f"{brand} — {name}"

    # ── Image local file ──────────────────────────────────────────
    local = p.get("image_local", "")
    if not local:
        missing_image_file.append(label)
    else:
        fpath = local if os.path.isabs(local) else os.path.join(os.path.dirname(JSON_PATH), local)
        if not os.path.exists(fpath):
            missing_image_file.append(f"{label}  [file missing: {local}]")

    # ── Image URL ─────────────────────────────────────────────────
    if not p.get("image_url"):
        missing_image_url.append(label)

    # ── Notes ─────────────────────────────────────────────────────
    has_any_notes = any(p.get(f) for f in note_fields)
    if not has_any_notes:
        missing_notes.append(label)

    # ── Vote fields ───────────────────────────────────────────────
    missing_in_p = []
    for vf in vote_fields:
        val = p.get(vf)
        if val is None or val == {} or val == []:
            missing_in_p.append(vf)
    if missing_in_p:
        missing_any_vote.append((label, missing_in_p))
        for vf in missing_in_p:
            missing_vote_data[vf].append(label)

    # ── URL ───────────────────────────────────────────────────────
    url = p.get("url", "")
    if not url:
        missing_url.append(label)
    elif not url_pattern.match(url):
        bad_url.append(f"{label}  [{url}]")

    # ── Description ──────────────────────────────────────────────
    desc = p.get("description", "")
    if not desc:
        no_description.append(label)
    elif len(desc) < 80:
        short_description.append(f"{label}  ({len(desc)} chars)")

# ── Note images ───────────────────────────────────────────────────
all_notes = set()
for p in perfumes:
    for f in note_fields:
        for n in (p.get(f) or []):
            all_notes.add(n.strip())

missing_note_imgs = []
if os.path.isdir(NOTE_IMG_DIR):
    for n in sorted(all_notes):
        fname = n.lower().replace(" ", "_").replace("/", "_") + ".jpg"
        fpath = os.path.join(NOTE_IMG_DIR, fname)
        if not os.path.exists(fpath):
            missing_note_imgs.append(n)
else:
    print(f"[WARN] note_images directory not found: {NOTE_IMG_DIR}\n")

# ── Summary ───────────────────────────────────────────────────────
def section(title, items, limit=20):
    print(f"{'─'*60}")
    print(f"  {title}  ({len(items)} items)")
    print(f"{'─'*60}")
    for i in items[:limit]:
        if isinstance(i, tuple):
            print(f"  • {i[0]}   missing: {', '.join(i[1])}")
        else:
            print(f"  • {i}")
    if len(items) > limit:
        print(f"  ... and {len(items) - limit} more")
    print()

print("=" * 60)
print("  SCENTSCAPE DATA AUDIT REPORT")
print("=" * 60)
print(f"  Total perfumes : {total}")
print(f"  Total unique notes: {len(all_notes)}")
print()

section("MISSING LOCAL IMAGE FILE", missing_image_file)
section("MISSING IMAGE URL", missing_image_url)
section("MISSING NOTES (no top/middle/base)", missing_notes)
section("MISSING ANY VOTE FIELD", missing_any_vote, limit=30)
section("MISSING URL", missing_url)
section("BAD/UNEXPECTED URL FORMAT", bad_url)
section("NO DESCRIPTION", no_description, limit=20)
section("SHORT DESCRIPTION (<80 chars)", short_description, limit=20)

print("=" * 60)
print("  PER-FIELD MISSING COUNT")
print("=" * 60)
for vf in vote_fields:
    cnt = len(missing_vote_data[vf])
    pct = cnt / total * 100
    bar = "█" * int(pct / 2) + "░" * (50 - int(pct / 2))
    print(f"  {vf:<15} {cnt:>5} / {total}  ({pct:5.1f}%)  {bar}")
print()

# ── Note image summary ────────────────────────────────────────────
print("=" * 60)
print(f"  NOTE IMAGES MISSING: {len(missing_note_imgs)} / {len(all_notes)}")
print("=" * 60)
for n in missing_note_imgs[:30]:
    print(f"  • {n}")
if len(missing_note_imgs) > 30:
    print(f"  ... and {len(missing_note_imgs) - 30} more")
print()

# ── Overall health score ──────────────────────────────────────────
checks = {
    "Has local image"   : total - len(missing_image_file),
    "Has image URL"     : total - len(missing_image_url),
    "Has notes"         : total - len(missing_notes),
    "Has all vote data" : total - len(missing_any_vote),
    "Has URL"           : total - len(missing_url),
    "Has description"   : total - len(no_description),
}
print("=" * 60)
print("  HEALTH OVERVIEW")
print("=" * 60)
for k, v in checks.items():
    pct = v / total * 100
    print(f"  {k:<22} {v:>5} / {total}  ({pct:5.1f}%)")
print()
