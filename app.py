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

# Serve perfume images and note images
app.mount("/images", StaticFiles(directory="perfume_images"), name="images")
app.mount("/note_images", StaticFiles(directory="perfume_notes"), name="note_images")
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
    note: Optional[List[str]] = Query(None),
    season: Optional[List[str]] = Query(None),
    accord: Optional[List[str]] = Query(None),
    price: Optional[str] = Query(None),
    longevity: Optional[List[str]] = Query(None),
    sillage: Optional[List[str]] = Query(None),
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
        note_list = [n.lower() for n in note]
        perfumes = [p for p in perfumes if all(
            any(nq in (nn or "").lower() for nn in (p.get("top_notes") or []) + (p.get("middle_notes") or []) + (p.get("base_notes") or []))
            for nq in note_list
        )]
    if accord:
        accord_list = [a.lower() for a in accord]
        perfumes = [p for p in perfumes if all(
            any(aq in acc.lower() for acc in (p.get('main_accords') or []))
            for aq in accord_list
        )]

    if price:
        price_key = price.lower()
        def get_dominant_price(p):
            pv = p.get('price_value')
            if not pv or not isinstance(pv, dict): return None
            return max(pv.items(), key=lambda x: x[1])[0] if pv else None
        
        perfumes = [p for p in perfumes if get_dominant_price(p) == price_key]
        # Sort by vote count for this price level
        perfumes.sort(key=lambda p: p.get('price_value', {}).get(price_key, 0), reverse=True)

    if longevity:
        lon_keys = [l.lower() for l in longevity]
        def get_dominant_longevity(p):
            lv = p.get('longevity')
            if not lv or not isinstance(lv, dict): return None
            return max(lv.items(), key=lambda x: x[1])[0] if lv else None
        
        perfumes = [p for p in perfumes if get_dominant_longevity(p) in lon_keys]
        # Sort by total votes for selected longevity levels
        perfumes.sort(key=lambda p: sum(p.get('longevity', {}).get(k, 0) for k in lon_keys), reverse=True)

    if sillage:
        sil_keys = [s.lower() for s in sillage]
        def get_dominant_sillage(p):
            sv = p.get('sillage')
            if not sv or not isinstance(sv, dict): return None
            return max(sv.items(), key=lambda x: x[1])[0] if sv else None
        
        perfumes = [p for p in perfumes if get_dominant_sillage(p) in sil_keys]
        # Sort by total votes for selected sillage levels
        perfumes.sort(key=lambda p: sum(p.get('sillage', {}).get(k, 0) for k in sil_keys), reverse=True)

    if season:
        season_keys = [s.lower() for s in season]
        SEASON_GROUP  = {'spring', 'summer', 'fall', 'winter'}
        DAYTIME_GROUP = {'day', 'night'}

        def get_dominant_values(p):
            sv = p.get("season")
            if not sv or not isinstance(sv, dict): return {'seasons': [], 'daytime': []}
            
            # Separate season and daytime votes
            season_votes = {k: v for k, v in sv.items() if k in SEASON_GROUP}
            daytime_votes = {k: v for k, v in sv.items() if k in DAYTIME_GROUP}
            
            result = {'seasons': [], 'daytime': []}
            
            # Get dominant seasons (allow multiple if close in votes)
            if season_votes:
                sorted_seasons = sorted(season_votes.items(), key=lambda x: x[1], reverse=True)
                top_votes = sorted_seasons[0][1]
                threshold = top_votes * 0.65  # 65% threshold for multi-season perfumes
                result['seasons'] = [s[0] for s in sorted_seasons if s[1] >= threshold]
            
            # Get dominant daytime (day/night) - both can be dominant
            if daytime_votes:
                # Include any daytime value with votes (day and night can both be dominant)
                result['daytime'] = [k for k, v in daytime_votes.items() if v > 0]
            
            return result
        
        def matches_season_filter(p):
            dominant = get_dominant_values(p)
            all_dominant = dominant['seasons'] + dominant['daytime']
            return any(s in all_dominant for s in season_keys)
        
        perfumes = [p for p in perfumes if matches_season_filter(p)]
        # Sort by total votes for selected seasons
        perfumes.sort(key=lambda p: sum(p.get('season', {}).get(k, 0) for k in season_keys), reverse=True)

    # Sort — always apply user's chosen sort, even after ratio-based filters
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
