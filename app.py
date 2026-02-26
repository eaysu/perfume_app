"""
Standalone Perfume Explorer - FastAPI backend
Serves perfume data directly from fragrantica_perfumes.json
"""
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import json
import os

app = FastAPI(title="Perfume Explorer", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve perfume images
app.mount("/images", StaticFiles(directory="perfume_images"), name="images")
app.mount("/static", StaticFiles(directory="static"), name="static")

DATA_FILE = "fragrantica_perfumes.json"

def load_perfumes():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/", response_class=HTMLResponse)
async def root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/perfumes")
async def get_perfumes(
    search: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    gender: Optional[str] = Query(None),
    note: Optional[str] = Query(None),
    season: Optional[str] = Query(None),
    accord: Optional[str] = Query(None),
    price: Optional[str] = Query(None),
    longevity: Optional[str] = Query(None),
    sillage: Optional[str] = Query(None),
    sort: str = Query("rating"),
    order: str = Query("desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(24, ge=1, le=1000),
):
    perfumes = load_perfumes()

    # Filters
    if search:
        q = search.lower()
        perfumes = [p for p in perfumes if q in p.get("name", "").lower() or q in p.get("brand", "").lower()]
    if brand:
        perfumes = [p for p in perfumes if p.get("brand", "").lower() == brand.lower()]
    if category:
        perfumes = [p for p in perfumes if p.get("category", "").lower() == category.lower()]
    if gender:
        perfumes = [p for p in perfumes if (p.get("gender") or "").lower() == gender.lower()]
    if note:
        n = note.lower()
        perfumes = [p for p in perfumes if any(
            n in (nn or "").lower()
            for nn in (p.get("top_notes") or []) + (p.get("middle_notes") or []) + (p.get("base_notes") or [])
        )]
    if accord:
        a = accord.lower()
        perfumes = [p for p in perfumes if any(
            a in acc.lower() for acc in (p.get('main_accords') or [])
        )]

    if price:
        price_key = price.lower()
        PRICE_LEVELS = ['way_overpriced', 'overpriced', 'ok', 'good_value', 'great_value']
        def price_ratio(p):
            pv = p.get('price_value')
            if not pv or not isinstance(pv, dict): return 0
            val = pv.get(price_key, 0)
            total = sum(pv.values())
            return val / total if total else 0
        perfumes = [p for p in perfumes if price_ratio(p) > 0]
        perfumes.sort(key=price_ratio, reverse=True)

    if longevity:
        lon_key = longevity.lower()
        def lon_ratio(p):
            lv = p.get('longevity')
            if not lv or not isinstance(lv, dict): return 0
            val = lv.get(lon_key, 0)
            total = sum(lv.values())
            return val / total if total else 0
        perfumes = [p for p in perfumes if lon_ratio(p) > 0]
        perfumes.sort(key=lon_ratio, reverse=True)

    if sillage:
        sil_key = sillage.lower()
        def sil_ratio(p):
            sv = p.get('sillage')
            if not sv or not isinstance(sv, dict): return 0
            val = sv.get(sil_key, 0)
            total = sum(sv.values())
            return val / total if total else 0
        perfumes = [p for p in perfumes if sil_ratio(p) > 0]
        perfumes.sort(key=sil_ratio, reverse=True)

    if season:
        s = season.lower()
        SEASON_GROUP  = {'spring', 'summer', 'fall', 'winter'}
        DAYTIME_GROUP = {'day', 'night'}

        def season_ratio(p):
            sv = p.get("season")
            if not sv or not isinstance(sv, dict): return 0
            val = sv.get(s, 0)
            if not val: return 0
            # Normalize within the relevant group
            if s in SEASON_GROUP:
                group_total = sum(sv.get(k, 0) for k in SEASON_GROUP)
            else:
                group_total = sum(sv.get(k, 0) for k in DAYTIME_GROUP)
            return val / group_total if group_total else 0

        perfumes = [p for p in perfumes if season_ratio(p) > 0]
        perfumes.sort(key=season_ratio, reverse=True)

    # Sort — skip if a ratio-based filter already ordered results
    if not season and not price and not longevity and not sillage:
        reverse = order == "desc"
        if sort == "rating":
            perfumes.sort(key=lambda p: p.get("rating") or 0, reverse=reverse)
        elif sort == "votes":
            perfumes.sort(key=lambda p: p.get("votes") or 0, reverse=reverse)
        elif sort == "name":
            perfumes.sort(key=lambda p: p.get("name") or "", reverse=reverse)
        elif sort == "brand":
            perfumes.sort(key=lambda p: p.get("brand") or "", reverse=reverse)
        elif sort == "year":
            perfumes.sort(key=lambda p: p.get("release_year") or 0, reverse=reverse)

    total = len(perfumes)
    start = (page - 1) * limit
    page_data = perfumes[start:start + limit]

    # Fix image paths
    for p in page_data:
        local = p.get("image_local", "")
        if local:
            filename = os.path.basename(local)
            p["image_path"] = f"/images/{filename}"

    return {"total": total, "page": page, "limit": limit, "perfumes": page_data}


@app.get("/api/accords")
async def get_accords():
    perfumes = load_perfumes()
    from collections import Counter
    counts = Counter(
        acc for p in perfumes
        for acc in (p.get('main_accords') or [])
        if acc
    )
    return sorted([{"name": a, "count": c} for a, c in counts.items()], key=lambda x: -x["count"])


@app.get("/api/brands")
async def get_brands():
    perfumes = load_perfumes()
    from collections import Counter
    counts = Counter(p.get("brand", "") for p in perfumes)
    return sorted([{"name": b, "count": c} for b, c in counts.items()], key=lambda x: x["name"])


@app.get("/api/notes")
async def get_notes():
    perfumes = load_perfumes()
    all_notes = set()
    for p in perfumes:
        for field in ["top_notes", "middle_notes", "base_notes"]:
            for n in (p.get(field) or []):
                if n:
                    all_notes.add(n)
    return sorted(all_notes)


@app.get("/api/stats")
async def get_stats():
    perfumes = load_perfumes()
    brands = set(p.get("brand") for p in perfumes)
    all_notes = set()
    for p in perfumes:
        for field in ["top_notes", "middle_notes", "base_notes"]:
            for n in (p.get(field) or []):
                if n:
                    all_notes.add(n)
    rated = [p for p in perfumes if p.get("rating")]
    avg_rating = sum(p["rating"] for p in rated) / len(rated) if rated else 0
    return {
        "total_perfumes": len(perfumes),
        "total_brands": len(brands),
        "total_notes": len(all_notes),
        "avg_rating": round(avg_rating, 2),
    }
